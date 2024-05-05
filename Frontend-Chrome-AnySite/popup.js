const urlInput = document.getElementById("url-input-field");
const colTolInput = document.getElementById("coltol-input-field");
const nameTolInput = document.getElementById("name-input-field");
const charTolInput = document.getElementById("char-input-field");
const colStrideInput = document.getElementById("colstride-input-field");
const websitesInput = document.getElementById("websites-input-field");
const addSiteButton = document.getElementById("addsite");
const runButton = document.getElementById("run");
const stopButton = document.getElementById("stop");
const testApiButton = document.getElementById("test-api");

chrome.storage.local.get(["apiURL", "colTol", "nameStr", "charStr", "colStride", "websites"], (result) => {
    urlInput.value = result.apiURL || "https://127.0.0.1:5000";
    colTolInput.value = result.colTol || "180";
    nameTolInput.value = result.nameStr || "";
    charTolInput.value = result.charStr || "";
    colStrideInput.value = result.colStride || "4";
    websitesInput.value = result.websites || "mangadex.org\nchapmanganelo.com\nfanfox.net";
    const sitesArray = websitesInput.value.split("\n");
    websitesInput.rows = sitesArray.length + 1
    websitesInput.cols = sitesArray.reduce((len, str) => { return Math.max(len, str.length) }, 25);
    addSiteButton.style.display = "none"
    chrome.tabs.query({currentWindow: true, active: true}, (tabs) => {
        if (tabs[0]?.url?.startsWith("http")) {
            const hostname = new URL(tabs[0].url).hostname;
            if (hostname && !websitesInput.value.includes(hostname)) {
                addSiteButton.innerText = "Add " + hostname;
                addSiteButton.removeAttribute("style");
                addSiteButton.addEventListener("click",() => {
                    addSiteButton.style.display = "none"
                    if (websitesInput.value.length > 0 && !websitesInput.value.endsWith("\n"))
                        websitesInput.value += "\n";
                    websitesInput.value += hostname;
                    chrome.storage.local.set({websites: websitesInput.value.trim()});
                });
            }
        }
    });
});

testApiButton.addEventListener("click",() => {
    chrome.tabs.create({url: urlInput.value, selected: true, active: true});
})

runButton.addEventListener("click",() => {
    chrome.storage.local.set({
        apiURL: urlInput.value.trim(),
        colTol: colTolInput.value.trim(),
        nameStr: nameTolInput.value.trim(),
        charStr: charTolInput.value.trim(),
        colStride: colStrideInput.value.trim(),
        running: true,
        websites: websitesInput.value.trim(),
        currentTab: true,
    });
})


stopButton.addEventListener("click",() => {
    chrome.storage.local.set({
        apiURL: urlInput.value.trim(),
        colTol: colTolInput.value.trim(),
        nameStr: nameTolInput.value.trim(),
        charStr: charTolInput.value.trim(),
        colStride: colStrideInput.value.trim(),
        running: false,
        websites: websitesInput.value.trim(),
        currentTab: true,
    });
})