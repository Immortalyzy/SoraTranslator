# GalTransl Progress Manual Checklist

## Preconditions

- Backend is running.
- Frontend is running.
- Translator is set to `galtransl` in preferences.
- Project contains at least one non-empty text file.

## Checklist

1. Start `Translate all files` in GalTransl mode.
2. Confirm the translation status area switches from `Idle` to `Preparing` then `Translating`.
3. Confirm `x/y` progress changes while translation is running.
4. Confirm the file hint updates as output JSON files are produced.
5. Confirm no second GalTransl run can start while one is active (shows busy/conflict message).
6. Confirm when translation finishes, spinner stops and status becomes `Completed`.
7. Confirm directory tree/status refresh occurs and translated files can be opened.
8. Force a backend translation error (for example invalid runtime credentials) and confirm status becomes `Failed` with error text.
9. Switch translator to `gpt`, run `Translate this file`, and confirm existing GPT progress behavior still works.
