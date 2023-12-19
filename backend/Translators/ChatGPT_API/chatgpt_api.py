""" This file contains the ChatGPT API for translation. """

from datetime import datetime
from openai import OpenAI
from ...scriptfile import ScriptFile
from ...constants import Config, default_config
from ...constants import SuccessStatus as success
from ...logger import log_message



class GPT_Translator:
    """ This class contains the ChatGPT API for translation. """

    def __init__(self, config: Config = default_config) -> None:
        """ This method initializes the ChatGPT API for translation. """
        self.client = OpenAI(api_key=config.openai_api_key)

        self.config = config
        self.model = config.gpt_model

    def translate(self, script_file: ScriptFile) -> success:
        """ This method translates the script_file into the specified language. """
        # todo: separate to translate_file() and translate_block()
        # todo: add function of reading half-transalted file
        # todo: estimate the total tokens in the file, if below allowable limit, translate the whole file in a single request.
        # initiate the translator
        base_message = self.config.gpt_prompt
        total_message = base_message
        all_contexts = []
        success_blocks = 0

        for block in script_file.blocks:
            # translate each block
            # if the block has been translated, skip
            if block.is_translated or block.is_empty():
                continue

            total_message = base_message.copy()
            # add context
            if self.config.gpt_context_block_count == 0:
                total_message.extend(all_contexts)
            else:
                # Determine the number of context blocks to include
                context_block_count = min(len(all_contexts) // 2, self.config.gpt_context_block_count)

                # Calculate the starting index to center the blocks if possible
                start_index = max((len(all_contexts) // 2) - context_block_count, 0)

                # Select the desired context blocks
                selected_contexts = all_contexts[start_index * 2:(start_index + context_block_count) * 2]

                # Append the selected contexts to the total_message list
                total_message.extend(selected_contexts)

            # original text
            text_original = block.text_original
            #todo: decide whether to add a speaker

            # add query
            total_message.append({"role": "user", "content": text_original})

            # get the response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=total_message,
                n=1, # number of response choicesd
                temperature=self.config.gpt_temperature,
                max_tokens=self.config.gpt_completion_max_tokens,
                stop=["\n"],
                stream=False,
            )

            # extract response message
            translation = response.choices[0].message.content.replace('\n\n', '\n').strip()

            # check success status
            # if the translation response contains one of failure keywords
            if any(keyword in translation for keyword in self.config.failure_keywords):
                block.is_translated = False
                if self.config.record_failure_text:
                    block.text_translated = translation
                    block.translation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            else:
                success_blocks += 1

                # record the translation
                block.text_translated = translation

                # add context only if the translation succeded to avoid polluting the context
                all_contexts.append({"role": "user", "content": text_original})
                all_contexts.append({"role": "assistant", "content": translation})

                # update the translation info
                block.is_translated = True
                block.translation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                block.translation_engine = self.config.gpt_model


            log_message(f"Translated block {block.block_name} ")


        # calculate success status, if the file is empty, return SUCCESS
        success_status = success.status_from_ratio(success_blocks/len(script_file.blocks)) if len(script_file.blocks) > 0 else success.SUCCESS

        # translate blocks
        return success_status

    @staticmethod
    def count_tokens(text: str) -> int:
        """ This method counts the number of tokens in the text. """
        # todo: implement this
        return len(text.split(" "))
