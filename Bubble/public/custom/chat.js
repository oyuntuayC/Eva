// initialize by constructing a named function...
// ...and add text processing plugin:

function makeid() {
  var result = "";
  var characters =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  var charactersLength = characters.length;
  for (var i = 0; i < 20; i++) {
    result += characters.charAt(
      Math.floor(Math.random() * charactersLength)
    );
  }
  return result;
}

//modify height
document.querySelector("#chat").style.height=window.innerHeight

//the base url at which RASA is running
var base_url = window.location.origin;

//A unique client id so that the data doesn't get mismatched
var client_id = makeid();

//add language option listener
var language='en'
const mapping={en:'en-US',ca:'ca-ES',es:'es-ES',zh:'zh-CN'}
//request list of voices
function getVoice(){
  let voices = [];
  voices = window.speechSynthesis.getVoices();
  var voice_id = 0;
  for (let i = 0; i < voices.length; i++) {
    if (voices[i].lang ==mapping[language]) {
      voice_id = i;
      break;
    }
  }
  return voice_id
}
var voice_id=0;

var chatWindow = new Bubbles(
  document.getElementById("chat"),
  "chatWindow",
  {
    // the one that we care about is inputCallbackFn()
    // this function returns an object with some data that we can process from user input
    // and understand the context of it

    // this is an example function that matches the text user typed to one of the answer bubbles
    inputCallbackFn: function (chatObject) {
      var miss = function (text_inp = null) {
        var xhr = new XMLHttpRequest();
        var url = base_url + "/webhooks/rest/webhook";

        //translate
        var result = translate(chatObject.input, language, 'en')
      
        var input = false;
        if (text_inp) {
          input = text_inp;
        } else {
          input = chatObject.input;
        }

        // RASA's POST format
        var request_body = {
          sender: client_id,
          message: result,
        };

        xhr.onreadystatechange = function () {
          if (xhr.readyState == XMLHttpRequest.DONE) {
            response = JSON.parse(xhr.responseText);

            var answers = [];
            var re = [];

            for (i = 0; i < response.length; i++) {
              if (response[i]["recipient_id"] == client_id) {
                //We check if the reponse by RASA contains any images
                if (response[i]["image"]) {
                  answers.push(
                    "<img src='" + response[i]["image"] + "'>"
                  );
                } else if (response[i]["text"]) {
                  var result = translate(response[i]["text"],'en',language);
                  answers.push(result);
                  //SpeechSynthesis
                  var msg = new SpeechSynthesisUtterance(result);
                  msg.voice = voices[voice_id]
                  window.speechSynthesis.speak(msg);
                }else if (response[i]["custom"]) {
                  for (j = 0; j < response[i]["custom"].length; j++) {
                    answers.push(
                      response[i]["custom"][j]
                    );
                  }
                }
                // Checks if there are buttons for the RASA response
                if (response[i]["buttons"]) {
                  for (j = 0; j < response[i]["buttons"].length; j++) {
                    re.push({
                      question: response[i]["buttons"][j]["title"],
                      answer: response[i]["buttons"][j]["payload"],
                    });
                  }
                }

              } else {
                console.log("Wrong client id");
              }
            }

            chatWindow.talk(
              {
                talk: {
                  says: answers,
                  reply: re,
                },
              },
              "talk"
            );
          }
        };

        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.send(JSON.stringify(request_body));
      };

      var found = false;
      if (chatObject.e) {
        chatObject.convo[chatObject.standingAnswer].reply.forEach(
          function (e, i) {
            strip(e.question).incldues(strip(chatObject.input)) &&
            chatObject.input.length > 0
              ? (found = e.answer)
              : found
              ? null
              : (found = false);
          }
        );
      } else {
        found = false;
      }

      miss(found);
    },

    //This function is called when the user clicks on a bubble button option. This callback is useful for the tasks that require dynamic handling of input rather than a static approach(like NLC).
    responseCallbackFn: function (chatObject, key) {
      var xhr = new XMLHttpRequest();
      var url = base_url + "/webhooks/rest/webhook";

      var input = key;
      var request_body = {
        sender: client_id,
        message: input,
      };

      xhr.onreadystatechange = function () {
        if (xhr.readyState == XMLHttpRequest.DONE) {
          response = JSON.parse(xhr.responseText);

          var answers = [];
          var re = [];

          for (i = 0; i < response.length; i++) {
            if (response[i]["recipient_id"] == client_id) {
              //We check if the reponse by RASA contains any images
              if (response[i]["image"]) {
                answers.push(
                  "<img src='" + response[i]["image"] + "'>"
                );
              } else if(response[i]["text"]){
                var result = translate(response[i]["text"],'en',language);
                answers.push(result);
                //SpeechSynthesis
                var msg = new SpeechSynthesisUtterance(result);
                msg.voice = voices[voice_id]
                window.speechSynthesis.speak(msg);
              }else if (response[i]["custom"]) {
                for (j = 0; j < response[i]["custom"].length; j++) {
                  answers.push(
                    response[i]["custom"][j]
                  );
                }
              }
              // Checks if there are buttons for the RASA response
              if (response[i]["buttons"]) {
                for (j = 0; j < response[i]["buttons"].length; j++) {
                  re.push({
                    question: response[i]["buttons"][j]["title"],
                    answer: response[i]["buttons"][j]["payload"],
                  });
                }
              }

            } else {
              console.log("Wrong client id");
            }
          }

          chatWindow.talk(
            {
              talk: {
                says: answers,
                reply: re,
              },
            },
            "talk"
          );
        }
      };

      xhr.open("POST", url, true);
      xhr.setRequestHeader("Content-Type", "application/json");
      xhr.send(JSON.stringify(request_body));
    },
  }
);

var convo = {
  ice: {
    says: ["Hi"],
  },
};

chatWindow.talk(convo);