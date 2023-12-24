""" This file contains the ChatGPT API for translation. """

from datetime import datetime
from openai import OpenAI
from ...scriptfile import ScriptFile
from ...block import Block
from ...constants import Config, default_config
from ...constants import SuccessStatus as success
from ...constants import LogLevel
from ...logger import log_message
from .. import utils


class GPT_Translator:
    """This class contains the ChatGPT API for translation."""

    def __init__(self, config: Config = default_config) -> None:
        """This method initializes the ChatGPT API for translation."""
        self.client = OpenAI(api_key=config.openai_api_key)

        self.config = config
        self.model = config.gpt_model

    def translate_block(self, block: Block, context=None) -> success:
        """translate a single block"""
        base_message = self.config.gpt_prompt
        total_message = base_message.copy()
        if context is not None:
            total_message.extend(context)
        total_message.append(
            {
                "role": "user",
                "content": block.text_to_translate(
                    self.config.if_translate_with_speaker
                ),
            }
        )
        # get the response
        response = self.client.chat.completions.create(
            model=self.model,
            messages=total_message,
            n=1,  # number of response choicesd
            temperature=self.config.gpt_temperature,
            max_tokens=self.config.gpt_completion_max_tokens,
            stop=["\n"],
            stream=False,
        )

        # extract response message
        translation = response.choices[0].message.content.replace("\n\n", "\n").strip()
        block.translation_status = response.choices[0].finish_reason

        # check success status
        # if the translation response contains one of failure keywords
        if not response.choices[0].finish_reason == "stop":
            block.is_translated = False
            if self.config.record_failure_text:
                block.text_translated = translation
                block.translation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message(
                f"Translation of block {block.block_name} failed.",
                log_level=LogLevel.DEBUG,
            )
            return success.ERROR

        else:
            # record the translation
            block.text_translated = translation

            # update the translation info
            block.is_translated = True
            block.translation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            block.translation_engine = self.config.gpt_model
            log_message(
                f"Translated block {block.block_name} successfully.",
                log_level=LogLevel.DEBUG,
            )
            return success.SUCCESS

    def translate_file_linebyline(self, script_file: ScriptFile) -> success:
        """This method translates the script_file into the specified language line by line.
        You should limit the number of context to consider or this will use a lot of tokens.
        """
        # initiate the translator
        all_contexts = []
        success_blocks = 0

        for block in script_file.blocks:
            # translate each block
            # if the block has been translated, skip
            if block.is_translated or block.is_empty():
                continue

            contexts = []
            # add context
            if self.config.gpt_context_block_count == 0:
                contexts = all_contexts.copy()
            else:
                # Determine the number of context blocks to include
                context_block_count = min(
                    len(all_contexts) // 2, self.config.gpt_context_block_count
                )

                # Calculate the starting index to center the blocks if possible
                start_index = max((len(all_contexts) // 2) - context_block_count, 0)

                # Select the desired context blocks
                contexts = all_contexts[
                    start_index * 2 : (start_index + context_block_count) * 2
                ]

            success_status = self.translate_block(block, contexts)
            success_blocks += 1 if success_status == success.SUCCESS else 0
            # END of iteration over blocks

        # calculate success status, if the file is empty, return SUCCESS
        success_status = (
            success.status_from_ratio(success_blocks / len(script_file.blocks))
            if len(script_file.blocks) > 0
            else success.SUCCESS
        )
        log_message(
            f"Translated {success_blocks} of {len(script_file.blocks)} blocks in file {script_file.text_file_path}.",
            log_level=LogLevel.INFO,
        )

        # translate blocks
        return success_status

    def translate_file_whole(self, script_file: ScriptFile) -> success:
        """This method translates the script_file into the specified language in a single time."""
        # todo: estimate the total tokens in the file, if below allowable limit, translate the whole file in a single request.
        # generate the messages
        all_text_list = []
        total_number_of_blocks_to_translate = 0
        for block in script_file.blocks:
            # if the block has been translated, skip
            if block.is_translated or block.is_empty():
                continue
            if utils.find_aaaa(block.text_original) is not None:
                continue
            all_text_list.append(
                block.text_to_translate(self.config.if_translate_with_speaker)
            )
            total_number_of_blocks_to_translate += 1

        # generate all_texts
        all_texts = "||".join(all_text_list)

        # generate the message
        base_message = self.config.gpt_prompt
        total_message = base_message.copy()
        total_message.append({"role": "user", "content": all_texts})

        # todo: add verification of total tokens, if larger than max_tokens/2, raise a warning

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=total_message,
                n=1,  # number of response choicesd
                temperature=self.config.gpt_temperature,
                max_tokens=self.config.gpt_completion_max_tokens,
                stop=["\n"],
                stream=False,
            )

            # extract response message
            translation = (
                response.choices[0].message.content.replace("\n\n", "\n").strip()
            )

            # divide to translations of each block
            translations = translation.split("||")
            if len(translations) != total_number_of_blocks_to_translate:
                log_message(
                    f"Translation of file {script_file.text_file_path} failed. (Translation count mismatch)",
                    log_level=LogLevel.ERROR,
                )
                # still save the results
                translation_index = 0
                for block in script_file.blocks:
                    if block.is_translated or block.is_empty():
                        continue
                    # skip the block if it contains aaaa
                    if utils.find_aaaa(block.text_original) is not None:
                        continue
                    # record the translation
                    block.text_translated = translations[translation_index]
                    translation_index += 1

                    # update the translation info
                    block.is_translated = False
                    block.translation_date = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    block.translation_engine = self.config.gpt_model

                    if translation_index >= len(translations):
                        break
                return success.ERROR

            for block in script_file.blocks:
                if block.is_translated or block.is_empty():
                    continue
                if utils.find_aaaa(block.text_original) is not None:
                    continue
                block.translation_status = response.choices[0].finish_reason

            # check success status
            # if the translation response contains one of failure keywords
            if not response.choices[0].finish_reason == "stop":
                script_file.is_translated = False
                log_message(
                    f"Translation of file {script_file.text_file_path} failed.",
                    log_level=LogLevel.DEBUG,
                )
                return success.ERROR

            else:
                log_message(
                    f"Translated file {script_file.text_file_path} successfully.",
                    log_level=LogLevel.DEBUG,
                )
                translation_index = 0
                for block in script_file.blocks:
                    if block.is_translated or block.is_empty():
                        continue
                    if utils.find_aaaa(block.text_original) is not None:
                        continue
                    # record the translation
                    block.text_translated = translations[translation_index]
                    translation_index += 1

                    # update the translation info
                    block.is_translated = True
                    block.translation_date = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    block.translation_engine = self.config.gpt_model

                return success.SUCCESS
        except:
            return success.ERROR

    @staticmethod
    def count_tokens(text: str) -> int:
        """This method counts the number of tokens in the text."""
        # todo: implement this
        return len(text.split(" "))
