function translate(text, languageIn, languageOut) {
  const url = `https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&sl=${encodeURI(languageIn)}&tl=${encodeURI(languageOut)}&q=${encodeURI(text)}`;

  const xhr = new XMLHttpRequest();
  xhr.open('GET', url, false);
  xhr.send();

  if (xhr.status === 200) {
    const data = JSON.parse(xhr.responseText);
    const result = data[0][0][0].replace(/^["“”「」‘’`]+|["“”「」‘’`]+$/g, '');
    return result;
  } else {
    throw new Error(`Failed to translate '${text}'. Status code: ${xhr.status}`);
  }
}

var languageSelector='<div class="language-selector" style="display: none;">\
  <label for="language" style="color: white;">Choose your language:</label>\
  <select id="language" name="language">\
    <option value="en">Select Language</option>\
    <option value="en">English</option>\
    <option value="ca">Catalan</option>\
    <option value="es">Español</option>\
    <option value="zh">Chinese</option>\
  </select>\
  <div class="language-background" style="z-index: -999;">\
  </div>\
</div>'

document.querySelector("#chat").insertAdjacentHTML('afterbegin',languageSelector);

