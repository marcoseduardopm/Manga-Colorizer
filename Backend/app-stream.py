from os import error
import os
from flask import Flask, request, send_from_directory, url_for, jsonify, abort
from flask_cors import CORS

import matplotlib.pyplot as plt
import PIL.Image
import numpy as np
import base64, io
import urllib.request, urllib.error

from colorizator import MangaColorizator, distance_from_grayscale

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return 'Manga Colorizer is Up and Running!'

        
@app.route('/colorize-image-data', methods=['POST'])
def colorize_image_data():
    img_format = 'PNG'
    req_json = request.get_json()
    img_name = ((req_json.get('imgName')).rsplit("?",1))[0] #obtain only the part before ? (if there is a ?)
    if (img_name.lower().find(".png") == -1):
        img_name = img_name + ".png" 
    img_size = req_json.get('imgWidth')
    name_str = req_json.get('nameStr') #title name
    char_str = req_json.get('charStr')
    if (img_size > 0):
        img_size = closestDivisibleBy32(img_size)
    else:
        img_size = 576
    img_data = req_json.get('imgData')
    img_url = req_json.get('imgURL')
    if (img_data):
        img_metadata, img_data64 = img_data.split(',', 1)
        # print("img_metadata", img_metadata)
        orig_image_binary = base64.decodebytes(bytes(img_data64, encoding='utf-8'))
    elif (img_url): # did not find imgData, look for imgURL instead
        orig_image_binary = retrieve_image_binary(request, img_url)
    else:
        raise Exception("Neither imgData nor imgURL found in request JSON")

    imgio = io.BytesIO(orig_image_binary)
    image = PIL.Image.open(imgio) 

    if not img_data:
        coloredness = distance_from_grayscale(image)
        print(f'Image distance from grayscale: {coloredness}')
        if (coloredness > 1):
            # abort(415, description=f'Image already colored: {coloredness} > 1')
            response = jsonify({'msg': f'Image already colored: {coloredness} > 1'})
            save_image(img_name, name_str, char_str, image)
            return response

    class Configuration:
        def __init__(self):
            self.generator = 'networks/generator.zip'
            self.extractor = 'networks/extractor.pth'
            self.gpu = True
            self.denoiser = True
            self.denoiser_sigma = 25
            self.size = img_size
            self.use_cached = True

    args = Configuration()

    if args.gpu:
        device = 'cuda'
    else:
        device = 'cpu'
        
    colorizer = MangaColorizator(device, args.generator, args.extractor)   
    color_image = colorize_image(image, colorizer, args)
    color_image_data64 = img_to_base64_str(color_image)
    
    save_image(img_name, name_str, char_str, color_image)
    
    response = jsonify({'colorImgData': color_image_data64})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

def save_image(img_name, name_str, char_str, color_image): #image name, title name, charapter
    
    if (name_str != '' and char_str != ''):
        #colorization_path = os.path.join(f'manga/{name_str}/{char_str}/colored')
        colorization_path = os.path.join(f'manga/{name_str}/{char_str}')
        os.makedirs(colorization_path, exist_ok=True)
        save_path = os.path.join(colorization_path, img_name)
        plt.imsave(save_path, color_image)
        
def retrieve_image_binary(orig_req, url):
    # print("Original headers", orig_req.headers)
    headers={
        'User-Agent': orig_req.headers.get('User-Agent'),
        'Referer': request.referrer,
        'Origin': request.origin,
        'Accept': 'image/png;q=1.0,image/jpg;q=0.9,image/webp;q=0.7,image/*;q=0.5',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'identity' }
    # print("Retrieving", url, headers)
    try:
        req = urllib.request.Request(url, headers=headers)
        return urllib.request.urlopen(req).read()
    except urllib.error.URLError as e:
        print("URLError", e.reason)
        abort(500)
    except error as e2:
        print("Retrieve error", e2)
    return False        

def colorize_image(image, colorizer, args):
    colorizer.set_image((np.array(image).astype('float32') / 255), args.size, args.denoiser, args.denoiser_sigma)
    #colorized_img = colorizer.colorize()
    #return (img_to_base64_str(colorized_img))
    return colorizer.colorize()

# def img_from_base64(img64):
#     orig_image_binary = base64.decodebytes(bytes(img64, encoding='utf-8'))
#     imgio = io.BytesIO(orig_image_binary)
#     return mpimg.imread(imgio, format='PNG')

def img_to_base64_str(img):
    buffered = io.BytesIO()
    plt.imsave(buffered, img, format="PNG")
    buffered.seek(0)
    img_byte = buffered.getvalue()
    return "data:image/png;base64," + base64.b64encode(img_byte).decode('utf-8')

# Function to find the number closest 
# to n and divisible by 32
def closestDivisibleBy32(n):
    divby = 32
    q = int(n / divby)
    n1 = divby * q
    if((n * divby) > 0):
        n2 = (divby * (q + 1)) 
    else:
        n2 = (divby * (q - 1))
    if (abs(n - n1) < abs(n - n2)) :
        return n1
    return n2

if __name__ == '__main__':
    context = ('server.crt', 'server.key')
    app.run(host='0.0.0.0', port=5000, ssl_context=context)
