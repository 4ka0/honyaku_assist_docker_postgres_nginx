from django.conf import settings
from django.utils import timezone

from environs import Env
import deepl
from deepl.exceptions import DeepLException
from google.oauth2 import service_account
from google.cloud import translate  # For the advanced API (v3)
# from google.cloud import translate_v2 as translate  # For the basic API (v2)

from .models import Engine


def translation_direction(direction):
    """
    Method to determine the direction of the translation to be performed.
    DeepL accepts "en" as a source language code but not as a target language
    code (has to be either "en-us" or "en-gb"). "en-us" is set here.
    """

    if direction == "Ja>En":
        return "ja", "en-us"
    else:
        return "en", "ja"


def call_deepl_api(source_text, source_lang, target_lang):
    """
    Method for calling the DeepL API.
    Returns:
    result (str): the translation obtained from DeepL.
    usage (int): current monthly usage according to DeepL.
    """

    env = Env()
    env.read_env()

    result = ""
    usage = ""

    # Authenticate with DeepL
    try:
        translator = deepl.Translator(env.str("DEEPL_AUTH_KEY"))
    except DeepLException as e:
        result = "(DeepL authentication error: " + str(e) + ")"
        usage = "(Unknown)"
        return result, usage

    # Get translation from DeepL
    try:
        result = translator.translate_text(
                source_text,
                source_lang=source_lang,
                target_lang=target_lang,
                glossary=None,
            )
    except DeepLException as e:
        result = "(DeepL translation error: " + str(e) + ")"
        usage = "(Unknown)"
        return result, usage

    # Get current usage from DeepL
    try:
        usage_obj = translator.get_usage()
        usage = usage_obj.character.count
    except DeepLException as e:
        usage = "(DeepL usage error: " + str(e) + ")"
        return result, usage

    return result, usage


def get_google_usage(source_text):
    """ Calculates the current usage for the Google engine taking into account
        the current source text that has been translated.
        The usage is reset for the current month if this has not already been
        done. """

    # Get Google engine object
    google_engine = Engine.objects.filter(name="Google")[0]

    # Update the Google usage value

    # Create a tuple representing the current month/year, e.g. (4, 2023).
    current_date = (timezone.now().month, timezone.now().year)

    # Create similar tuple for month/year the usage was last reset.
    last_reset_date = (
        google_engine.month_usage_last_reset,
        google_engine.year_usage_last_reset
    )

    # If the usage has not been reset for the current month.
    if last_reset_date != current_date:
        # Reset the usage value and update the usage date values
        google_engine.current_usage = len(source_text)
        google_engine.month_usage_last_reset = current_date[0]
        google_engine.year_usage_last_reset = current_date[1]
    else:
        # Simply add to the current usage
        google_engine.current_usage += len(source_text)

    google_engine.save()

    return google_engine.current_usage


def call_google_api_v3(source_text, source_lang, target_lang):
    """
    Method for calling the Google Translate API.
    Uses the Cloud Translation Advanced API (v3).
    Returns:
    result (str): the translation obtained from Google.
    usage (int): current monthly usage calculated locally.
    """

    env = Env()
    env.read_env()

    try:
        # Authenticate

        service_account_key = str(settings.BASE_DIR.joinpath(env.str("GOOGLE_PROJECT_CREDENTIALS")))

        credentials = service_account.Credentials.from_service_account_file(
            service_account_key
        )

        client = translate.TranslationServiceClient(credentials=credentials)

        # Translate

        project_id = env.str("GOOGLE_PROJECT_ID")
        location = "global"
        parent = f"projects/{project_id}/locations/{location}"

        response = client.translate_text(
            request={
                "parent": parent,
                "contents": [source_text],
                "mime_type": "text/plain",  # mime types: text/plain, text/html
                "source_language_code": source_lang,
                "target_language_code": target_lang,
            }
        )

        if response.translations[0].translated_text:
            result = response.translations[0].translated_text
        else:
            result = "(Error: Translation not included in response from Google)"

    except Exception as e:
        result = "(Error: " + str(e) + ")"

    usage = get_google_usage(source_text)

    return result, usage


'''
def call_google_api_v2(source_text, source_lang, target_lang):
    """
    Method for calling the Google Translate API.
    Uses the Cloud Translation Basic API (v2).
    """

    env = Env()
    env.read_env()

    google_service_account_key = str(settings.BASE_DIR.joinpath(env.str("GOOGLE_CREDENTIALS")))

    credentials = service_account.Credentials.from_service_account_file(
        google_service_account_key
    )

    translate_client = translate.Client(credentials=credentials)

    result = translate_client.translate(
        source_text,
        source_language=source_lang,
        target_language=target_lang,
    )

    return result["translatedText"]
'''
