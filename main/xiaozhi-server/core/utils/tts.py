import re
import importlib

from config.provider_profile import validate_provider_config, validate_provider_type
from core.utils.textUtils import check_emoji

punctuation_set = {
    "，",
    ",",  # Chinese and English commas.
    "。",
    ".",  # Chinese and English full stops.
    "！",
    "!",  # Chinese and English exclamation marks.
    "“",
    "”",
    '"',  # Chinese and English double quotation marks.
    "：",
    ":",  # Chinese and English colons.
    "-",
    "－",  # English hyphen and Chinese full-width dash.
    "、",  # Chinese enumeration comma.
    "[",
    "]",  # Square brackets.
    "【",
    "】",  # Chinese square brackets.
    "~",  # Tilde.
}

def create_instance(class_name, *args, **kwargs):
    validate_provider_type("TTS", class_name)
    config = args[0] if args else kwargs.get("config")
    validate_provider_config("TTS", config, class_name, require_ready=True)
    provider = importlib.import_module(f"core.providers.tts.{class_name}")
    return provider.TTSProvider(*args, **kwargs)


class MarkdownCleaner:
    """
    Markdown cleanup; call MarkdownCleaner.clean_markdown(text) directly.
    """
    # Formula characters.
    NORMAL_FORMULA_CHARS = re.compile(r'[a-zA-Z\\^_{}\+\-\(\)\[\]=]')

    @staticmethod
    def _replace_inline_dollar(m: re.Match) -> str:
        """
        For a complete "$...$" match:
          - Remove the surrounding $ signs if it contains typical formula characters.
          - Otherwise (numbers/currency, etc.), preserve "$...$".
        """
        content = m.group(1)
        if MarkdownCleaner.NORMAL_FORMULA_CHARS.search(content):
            return content
        else:
            return m.group(0)

    @staticmethod
    def _replace_table_block(match: re.Match) -> str:
        """
        Replace a matched table block with speakable text.
        Chinese narration below is user-language output, not maintainer prose.
        """
        block_text = match.group('table_block')
        lines = block_text.strip('\n').split('\n')

        parsed_table = []
        for line in lines:
            line_stripped = line.strip()
            if re.match(r'^\|\s*[-:]+\s*(\|\s*[-:]+\s*)+\|?$', line_stripped):
                continue
            columns = [col.strip() for col in line_stripped.split('|') if col.strip() != '']
            if columns:
                parsed_table.append(columns)

        if not parsed_table:
            return ""

        headers = parsed_table[0]
        data_rows = parsed_table[1:] if len(parsed_table) > 1 else []

        lines_for_tts = []
        if len(parsed_table) == 1:
            # A single row.
            only_line_str = ", ".join(parsed_table[0])
            lines_for_tts.append(f"单行表格：{only_line_str}")
        else:
            lines_for_tts.append(f"表头是：{', '.join(headers)}")
            for i, row in enumerate(data_rows, start=1):
                row_str_list = []
                for col_index, cell_val in enumerate(row):
                    if col_index < len(headers):
                        row_str_list.append(f"{headers[col_index]} = {cell_val}")
                    else:
                        row_str_list.append(cell_val)
                lines_for_tts.append(f"第 {i} 行：{', '.join(row_str_list)}")

        return "\n".join(lines_for_tts) + "\n"

    # Precompile regexes in execution-frequency order.
    # Define replacement static methods above this list so their references resolve.
    REGEXES = [
        (re.compile(r'```.*?```', re.DOTALL), ''),  # Code blocks.
        (re.compile(r'^#+\s*', re.MULTILINE), ''),  # Headings.
        (re.compile(r'(\*\*|__)(.*?)\1'), r'\2'),  # Bold.
        (re.compile(r'(\*|_)(?=\S)(.*?)(?<=\S)\1'), r'\2'),  # Italic.
        (re.compile(r'!\[.*?\]\(.*?\)'), ''),  # Images.
        (re.compile(r'\[(.*?)\]\(.*?\)'), r'\1'),  # Links.
        (re.compile(r'^\s*>+\s*', re.MULTILINE), ''),  # Block quotes.
        (
            re.compile(r'(?P<table_block>(?:^[^\n]*\|[^\n]*\n)+)', re.MULTILINE),
            _replace_table_block
        ),
        (re.compile(r'^\s*[*+-]\s*', re.MULTILINE), '- '),  # Lists.
        (re.compile(r'\$\$.*?\$\$', re.DOTALL), ''),  # Display formulas.
        (
            re.compile(r'(?<![A-Za-z0-9])\$([^\n$]+)\$(?![A-Za-z0-9])'),
            _replace_inline_dollar
        ),
        (re.compile(r'\n{2,}'), '\n'),  # Extra blank lines.
    ]

    @staticmethod
    def clean_markdown(text: str) -> str:
        """
        Main entry point: apply regexes in order to remove or replace Markdown elements.
        """
        for regex, replacement in MarkdownCleaner.REGEXES:
            text = regex.sub(replacement, text)

        # Remove emoji.
        text = check_emoji(text)

        # Check whether text contains only ASCII, whitespace and basic punctuation.
        if text and all((c.isascii() or c.isspace() or c in punctuation_set) for c in text):
            # Preserve the original whitespace and return directly.
            return text

        return text.strip()

def convert_percentage_to_range(percentage, min_val, max_val, base_val=None):
    """
    Convert a percentage (-100 to 100) to a value in the specified range.

    Args:
        percentage: Percentage value (-100 to 100).
        min_val: Minimum of the target range.
        max_val: Maximum of the target range.
        base_val: Optional base value; defaults to the range midpoint.

    Returns:
        The converted value.
    """
    percentage, min_val, max_val = float(percentage), float(min_val), float(max_val)
    base_val = float(base_val) if base_val is not None else (min_val + max_val) / 2

    if percentage < 0:
        # Negative percentage: interpolate linearly from base_val toward min_val.
        result = base_val + (base_val - min_val) * (percentage / 100)
    else:
        # Positive percentage: interpolate linearly from base_val toward max_val.
        result = base_val + (max_val - base_val) * (percentage / 100)

    # Clamp the result to the valid range.
    return max(min_val, min(max_val, result))
