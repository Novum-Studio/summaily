from mistral_common.protocol.instruct.tool_calls import Function, Tool
from mistral_inference.model import Transformer
from mistral_inference.generate import generate

from mistral_common.tokens.tokenizers.mistral import MistralTokenizer
from mistral_common.protocol.instruct.messages import UserMessage
from mistral_common.protocol.instruct.request import ChatCompletionRequest



class Summarizer:
    def __init__(self, model_path):
        self.model_path = model_path
        self.tokenizer = MistralTokenizer.from_file(f"{self.model_path}/tokenizer.model.v3")
        self.model = Transformer.from_folder(self.model_path)
    
    def summarize(self, email_body, category) -> str:
        category_str = ', '.join(category[:-1])
        category_str += f", or {category[-1]}"
        prompt = (
            "Please summarize the following email content. "
            f"After providing the summary, categorize the email into one of the following categories: {category_str}. "
            "The JSON format should look like this:\n"
            '{"summary": "<summary of the email>", "category": "<category>"}\n\n'
            "Here is the email content:\n\n"
            f"{email_body}\n\n"
            "Return only the JSON format."
        )


        completion_request = ChatCompletionRequest(
        tools=[
            Tool(
                function=Function(
                    name="get_email_summary",
                    description="Summarize the given email body, e.g. ",
                    parameters={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": category,
                                "description": "The category of this email, e.g. Others",
                            },
                            "summary": {
                                "type": "string",
                                "description": "The summary and important point of this email.",
                            },
                            
                        },
                        "required": ["summary", "category"],
                    },
                )
            )
        ],
        messages=[
            UserMessage(content=prompt),
            ],
        )
        tokens = self.tokenizer.encode_chat_completion(completion_request).tokens

        out_tokens, _ = generate([tokens], self.model, max_tokens=1000, temperature=0.0, eos_id=self.tokenizer.instruct_tokenizer.tokenizer.eos_id)
        result = self.tokenizer.instruct_tokenizer.tokenizer.decode(out_tokens[0])

        return result