var inputSwitch = document.querySelector("#chat > div.input-wrap > div.speech-switch");
var enterButton = document.createElement("div");
enterButton.setAttribute("class", "bubble language-button enter-button");
var svgEnter = document.createElement("img");
svgEnter.setAttribute("src", "./enter.svg");
svgEnter.setAttribute("style", "width:15px;height:15px;cursor:pointer;border-radius:0px !important;margin-top: 4px;");
enterButton.appendChild(svgEnter);
inputSwitch.appendChild(enterButton);

const keyboardEvent = new KeyboardEvent('keypress', {
    keyCode: 13,
    view: window,
    bubbles: true
  });

enterButton.onclick = function() {
    textArea.dispatchEvent(keyboardEvent);
}