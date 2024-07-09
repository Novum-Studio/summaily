from mistral_common.protocol.instruct.tool_calls import Function, Tool
from mistral_inference.model import Transformer
from mistral_inference.generate import generate

from mistral_common.tokens.tokenizers.mistral import MistralTokenizer
from mistral_common.protocol.instruct.messages import UserMessage
from mistral_common.protocol.instruct.request import ChatCompletionRequest
from typing import Tuple, Optional
import time
from .constants import LAZY_LOAD

def load_model(model_path : str) -> Tuple[MistralTokenizer, Transformer]:
    start = time.time()
    print("Loading tokenizer...")
    tokenizer = MistralTokenizer.from_file(f"{model_path}/tokenizer.model.v3")
    print(f"Tokenizer loaded in {time.time() - start:.2f} seconds")

    start = time.time()
    print("Loading model...")
    model = Transformer.from_folder(model_path)
    print(f"Model loaded in {time.time() - start:.2f} seconds")
    
    return tokenizer, model


class Summarizer:
    def __init__(self, model_path : str):
        self.model_path = model_path
        self.tokenizer: Optional[MistralTokenizer] = None
        self.model: Optional[Transformer] = None
        if not LAZY_LOAD:
            self.tokenizer, self.model = load_model(self.model_path)
        
    
    def summarize(self, email_body : str, category : list) -> str:
        if not self.tokenizer or not self.model:
            self.tokenizer, self.model = load_model(self.model_path)
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