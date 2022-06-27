import json
import openai
openai.api_key = "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"

class openai_Chatbot():
    def __init__(self):
        pass

    def ask(self, soru):
        response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=soru,
        temperature=0.1,
        max_tokens=200,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
        stop=[" Human:", " AI:"]
        )
        rez = json.loads(json.dumps(response))
        text = rez["choices"][0]['text']
        return text