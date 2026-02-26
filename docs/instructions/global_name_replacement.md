# add-global-name-replacement

## Background

During the integration phase of Chaos-R games (`./backend/Integrators/Chaos_R`), character names in the scripts are currently replaced only where they appear explicitly in the original script text.

However, some macros depend on these character names internally. Because of this, simple or partial name replacement is not sufficient. If names are not replaced consistently everywhere, the related macros may not work correctly.

---

## Goal

Create a global name replacement mechanism that ensures:

* Character names are managed in a single place.
* Users edit names only in that location.
* All decoded script files use the updated names consistently.
* Macros depending on these names continue to function properly.

---

## 1. Add a Fake Name Replacement Text File

Here is an illustraion of my text display window:
![Example text file display](../figs/translation_page.png)

Add a virtual (fake) text file that appears at the top of the file list in the text display window.

This file should:

* Contain a table of name replacements.
* Be the only place where users can edit character names.
* Control the name replacements applied to all other script files.

User edits in this file must affect all following script files.

---

## 2. Behavior During Integration

During the integration phase:

* After the translated text have been integrated into `TranslatedFiles`, but before the final output is generated,
* Perform a global find-and-replace operation.

Specifically:

* For each name defined in the fake replacement file,
* Replace all occurrences of that name
* In all decoded script files.

This ensures that:

* Macros that depend on these names are updated correctly.
* All scripts use the updated names consistently.
