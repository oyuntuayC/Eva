function translate(text, language) {
    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&sl=${encodeURI(language)}&tl=en&q=${encodeURI(text)}`;
    
    return fetch(url)
      .then(response => response.json())
      .then(data => {
        const result = data[0][0][0].replace(/^["“”「」‘’`]+|["“”「」‘’`]+$/g, '');
        return result;
      })
      .catch(error => {
        console.error(error);
      });
  }