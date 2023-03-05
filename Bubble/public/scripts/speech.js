var SpeechRecognition = SpeechRecognition || webkitSpeechRecognition
var SpeechGrammarList = SpeechGrammarList || window.webkitSpeechGrammarList
var SpeechRecognitionEvent = SpeechRecognitionEvent || webkitSpeechRecognitionEvent

var recognition = new SpeechRecognition();
// if (SpeechGrammarList) {
//   // SpeechGrammarList is not currently available in Safari, and does not have any effect in any other browser.
//   // This code is provided as a demonstration of possible capability. You may choose not to use it.
//   var speechRecognitionList = new SpeechGrammarList();
//   var grammar = '#JSGF V1.0; grammar colors; public <color> = ' + colors.join(' | ') + ' ;'
//   speechRecognitionList.addFromString(grammar, 1);
//   recognition.grammars = speechRecognitionList;
// }
recognition.continuous = false;
recognition.lang = 'en-US';
recognition.interimResults = false;
recognition.maxAlternatives = 1;

// Append speech button
var inputWrap = document.querySelector("#chat > div.input-wrap");
inputWrap.setAttribute("style", "display:flex;flex-direction:row");
var speechButton = document.createElement("button");
speechButton.setAttribute("class", "bubble");
speechButton.setAttribute("style", "width:35px;cursor:pointer")
var svgVoice = document.createElementNS('http://www.w3.org/2000/svg',"svg");
svgVoice.setAttribute("viewBox", "0 0 1024 1024");
var svgPath = document.createElementNS('http://www.w3.org/2000/svg',"path");
svgPath.setAttribute("d","M767.131725 469.974861c-14.246469 0-26.502607 11.43647-26.786063 25.616424-8.593725 115.736954-108.84601 206.318996-228.222865 206.318996-119.407554 0-220.098837-90.617857-228.691539-206.355835-2.27788-12.418844-13.126972-21.979594-26.204825-21.979594-14.151301 0-25.596981 12.45466-26.487258 26.380834C242.74665 633.357975 347.325473 740.423433 482.107179 754.455008L482.107179 914.409023c0 16.620539 13.544481 30.137391 30.224372 30.137391 16.647145 0 30.193673-13.515828 30.193673-30.137391L542.525224 754.455008C675.837462 740.221842 780.9965 632.182196 793.260825 499.705999l-0.00921 0C793.251615 485.281475 781.557272 469.974861 767.131725 469.974861z M512.029676 663.540392c97.863888 0 177.468924-79.305207 177.468924-176.812985L689.4986 273.750781c0-124.120902-79.605036-194.297195-177.468924-194.297195-40.698934 0-94.097098 25.361621-121.103172 51.922557 0 0-53.383838 43.554982-56.42715 158.665673 0 1.195222 0.11768 2.357697 0.207731 3.074012-0.11768 1.699712-0.207731 3.341095-0.207731 5.042853l0 188.568726C334.500377 584.235185 414.135088 663.540392 512.029676 663.540392zM394.473283 290.041816c4.176113-89.808422 42.875506-121.04689 42.875506-121.04689 20.97573-18.916838 47.529503-29.331026 74.68191-29.331026 66.116837-4.356214 117.92069 59.598376 117.675096 137.219221l0 201.191208c0 70.235644-53.109592 125.226073-117.675096 125.226073-64.567551 0-117.557416-57.169047-117.557416-127.435391L394.473283 290.041816z");
svgVoice.appendChild(svgPath);

speechButton.appendChild(svgVoice);
inputWrap.appendChild(speechButton);

speechButton.onclick = function() {
  recognition.start();
  console.log('Ready to receive a color command.');
}

recognition.onresult = function(event) {
  // The SpeechRecognitionEvent results property returns a SpeechRecognitionResultList object
  // The SpeechRecognitionResultList object contains SpeechRecognitionResult objects.
  // It has a getter so it can be accessed like an array
  // The first [0] returns the SpeechRecognitionResult at the last position.
  // Each SpeechRecognitionResult object contains SpeechRecognitionAlternative objects that contain individual results.
  // These also have getters so they can be accessed like arrays.
  // The second [0] returns the SpeechRecognitionAlternative at position 0.
  // We then return the transcript property of the SpeechRecognitionAlternative object
  var color = event.results[0][0].transcript;
  console.log('Result received: ' + color + '.');
  // bg.style.backgroundColor = color;
  console.log('Confidence: ' + event.results[0][0].confidence);
  var inputText = document.querySelector("#chat > div.input-wrap > textarea")
  inputText.value = color
  const keyboardEvent = new KeyboardEvent('keypress', {
    keyCode: 13,
    view: window,
    bubbles: true
  });
  inputText.dispatchEvent(keyboardEvent);
}

recognition.onspeechend = function() {
  recognition.stop();
}

recognition.onnomatch = function(event) {
  console.log("I didn't recognise that color.");
}

recognition.onerror = function(event) {
  console.log('Error occurred in recognition: ' + event.error);
}
