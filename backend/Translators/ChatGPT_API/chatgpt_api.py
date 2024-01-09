""" This file contains the ChatGPT API for translation. """

from datetime import datetime
from openai import OpenAI
from textfile import TextFile
from block import Block
from config import Config, default_config
from constants import SuccessStatus as success
from constants import LogLevel
from logger import log_message
from .. import utils
from .. import utils_post
from ..translator import Translator


class GPT_Translator(Translator):
    """This class contains the ChatGPT API for translation."""

    def __init__(self, config: Config = default_config) -> None:
        """This method initializes the ChatGPT API for translation."""
        super().__init__(config)
        self.client = OpenAI(api_key=config.openai_api_key)

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

    def translate_file_whole(self, text_file: TextFile) -> success:
        """This method translates the text_file into the specified language in a single time."""
        # check if the number of blocks exceed line limit
        text_file.need_manual_fix = False
        log_message(
            f"Translating file with model: {self.model}", log_level=LogLevel.INFO
        )
        if len(text_file.blocks) > self.config.gpt_max_lines:
            # log
            # if exceed, divide the file into multiple parts
            n_parts = len(text_file.blocks) // self.config.gpt_max_lines + 1
            n_blocks_per_part = len(text_file.blocks) // n_parts + 1
            all_parts = []
            log_message(
                f"File {text_file.text_file_path} has too many blocks dividing to {n_parts} parts with each having {n_blocks_per_part} blocks.",
                log_level=LogLevel.WARNING,
            )
            for i in range(n_parts):
                if i == n_parts - 1:
                    sub_blocks = text_file.blocks[i * n_blocks_per_part :]
                sub_blocks = text_file.blocks[
                    i * n_blocks_per_part : (i + 1) * n_blocks_per_part
                ]
                all_parts.append(sub_blocks)

            for i, part in enumerate(all_parts):
                description = (
                    f"part {i+1} of {n_parts} of file {text_file.text_file_path}"
                )
                success_translation = self.translate_once(
                    target=part, target_description=description
                )
                if success_translation == success.ERROR:
                    text_file.need_manual_fix = True
        else:
            # translate the whole file
            success_translation = self.translate_once(
                target=text_file, target_description=text_file.text_file_path
            )
            if success_translation == success.ERROR:
                text_file.need_manual_fix = True

        # evaluate the success status
        success_blocks = 0
        for block in text_file.blocks:
            if block.is_translated:
                success_blocks += 1
        translated_ratio = success_blocks / len(text_file.blocks)
        text_file.translation_percentage = translated_ratio

        success_status = success.status_from_ratio(translated_ratio)
        if (
            success_status == success.ALMOST_SUCCESS
            or success_status == success.SUCCESS
        ):
            log_message(
                f"Translated file {text_file.text_file_path} successfully.",
                log_level=LogLevel.INFO,
            )
        else:
            log_message(
                f"Translated file {text_file.text_file_path} failed.",
                log_level=LogLevel.WARNING,
            )
        text_file.is_translated = True
        if text_file.need_manual_fix:
            log_message(
                f"Manual fix required for file {text_file.text_file_path}.",
                log_level=LogLevel.WARNING,
            )
        return success_status

    def translate_once(
        self, target: TextFile or list(Block), target_description: str = ""
    ) -> success:
        """This method translates the text_file into the specified language in a single time."""
        log_message(
            f'Translating target " {target_description} "...', log_level=LogLevel.INFO
        )
        if isinstance(target, TextFile):
            all_blocks = target.blocks
        # if the target is a list of blocks
        elif isinstance(target, list):
            all_blocks = target

        # generate the messages
        all_text_list = []
        total_number_of_blocks_to_translate = 0
        for block in all_blocks:
            # if the block has been translated, skip
            if block.is_empty():
                continue
            if utils.find_aaaa(block.text_original) is not None:
                continue
            all_text_list.append(
                block.text_to_translate(self.config.if_translate_with_speaker)
            )
            block.text_translated = ""
            total_number_of_blocks_to_translate += 1

        # generate all_texts
        all_texts = utils.convert_prompt_response(
            all_text_list,
            seperation_method=self.config.gpt_speration_method,
            enclosing_joiner=self.config.gpt_enclosing_joiner,
        )

        # generate the message
        base_message = self.config.gpt_prompt
        total_message = base_message.copy()
        total_message.append({"role": "user", "content": all_texts})
        total_message.append(
            {"role": "user", "content": f"There are {len(all_text_list)} blocks."}
        )

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
            # find all '[' in the translation
            translations = utils.convert_prompt_response(
                translation,
                seperation_method=self.config.gpt_speration_method,
                enclosing_joiner=self.config.gpt_enclosing_joiner,
            )

            # if the translation count does not match the block count and the config allows second try
            if (
                len(translations) != total_number_of_blocks_to_translate
                and self.config.gpt_second_try
            ):
                log_message(
                    f"Translation of target {target_description} failed. (Translation count mismatch)"
                    + f"{len(translations)} instead of {total_number_of_blocks_to_translate}.",
                    log_level=LogLevel.ERROR,
                )
                log_message("Making gpt try again.", log_level=LogLevel.ERROR)
                total_message.append(
                    {"role": "assistant", "content": translation.strip()}
                )
                # generating the message again
                new_message = self.config.fixing_prompt
                new_message[0]["content"] = new_message[0]["content"].format(
                    len(translations), total_number_of_blocks_to_translate
                )
                total_message.append(new_message[0])

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=total_message,
                    n=1,  # number of response choicesd
                    temperature=self.config.gpt_temperature,
                    max_tokens=self.config.gpt_completion_max_tokens,
                    stop=["\n"],
                    stream=False,
                )
                translation = (
                    response.choices[0].message.content.replace("\n\n", "\n").strip()
                )

            if len(translations) != total_number_of_blocks_to_translate:
                # still save the results
                translation_index = 0
                log_message(
                    f"Translation of target {target_description} failed. (Translation count mismatch)"
                    + f"{len(translations)} instead of {total_number_of_blocks_to_translate}.",
                    log_level=LogLevel.ERROR,
                )
                for block in all_blocks:
                    if block.is_empty():
                        continue
                    # skip the block if it contains aaaa
                    if utils.find_aaaa(block.text_original) is not None:
                        continue
                    if translation_index >= len(translations):
                        break
                    # record the translation
                    block.text_translated = translations[translation_index]
                    block = utils_post.fix_text_after_translation(block)
                    translation_index += 1

                    # update the translation info
                    block.is_translated = False
                    block.translation_date = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    block.translation_engine = self.config.gpt_model

                return success.ERROR

            for block in all_blocks:
                if block.is_empty():
                    continue
                if utils.find_aaaa(block.text_original) is not None:
                    continue
                block.translation_status = response.choices[0].finish_reason

            # check success status
            # if the translation response contains one of failure keywords
            if not response.choices[0].finish_reason == "stop":
                log_message(
                    f"Translation of target {target_description} failed.",
                    log_level=LogLevel.DEBUG,
                )
                return success.ERROR

            else:
                log_message(
                    f"Translated target {target_description} successfully.",
                    log_level=LogLevel.DEBUG,
                )
                translation_index = 0
                for block in all_blocks:
                    if block.is_empty():
                        continue
                    if utils.find_aaaa(block.text_original) is not None:
                        continue
                    # record the translation
                    block.text_translated = translations[translation_index]
                    block = utils_post.fix_text_after_translation(block)
                    translation_index += 1

                    # update the translation info
                    block.is_translated = True
                    block.translation_date = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    block.translation_engine = self.config.gpt_model

                return success.SUCCESS
        except Exception as e:
            return success.ERROR

    @staticmethod
    def count_tokens(text: str) -> int:
        """This method counts the number of tokens in the text."""
        # todo: implement this
        return len(text.split(" "))
