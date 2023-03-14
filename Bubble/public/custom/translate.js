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