var inputSwitch = document.querySelector("#chat > div.input-wrap > div.speech-switch");
var languageButton = document.createElement("div");
languageButton.setAttribute("class", "bubble language-button");
var svgVoice = document.createElement("img");
svgVoice.setAttribute("src", "./translate.svg");
svgVoice.setAttribute("style", "width:22px;height:22px;cursor:pointer");
languageButton.appendChild(svgVoice);
inputSwitch.appendChild(languageButton);

var menu=document.querySelector("#chat > div.language-selector");
languageButton.onclick = function() {
    if (menu.style.display === "none") {
        menu.style.display = "flex";
      } else {
        menu.style.display = "none";
      }
}
var menubg=document.querySelector("#chat > div.language-selector > div.language-background")
menubg.onclick = function() {
  if (menu.style.display === "none") {
      menu.style.display = "flex";
    } else {
      menu.style.display = "none";
    }
}
var languageSelector = document.getElementById("language");
var menu=document.querySelector("#chat > div.language-selector");
languageSelector.addEventListener("change", function() {
    language = languageSelector.value;
    recognition.lang=mapping[language]
    menu.style.display = "none"
    voice_id=getVoice();
});
