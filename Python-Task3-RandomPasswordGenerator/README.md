# CipherCraft — Advanced Random Password Generator

A Tkinter desktop password generator using Python's cryptographically secure `secrets` module and the `pyperclip` clipboard library.

## Advanced-tier checklist
- [x] GUI with a Spinbox to choose password length (8–128).
- [x] Checkboxes for uppercase, lowercase, digits and symbols.
- [x] Uses `secrets`, never `random`, for password generation and shuffling.
- [x] Strength label (Weak / Medium / Strong) based on length and character diversity.
- [x] Guarantees at least one character from every selected character type.
- [x] Automatically copies each generated password using `pyperclip`; also provides a manual Copy button.
- [x] Checkbox to exclude ambiguous characters (`0`, `O`, `1`, `l`, `I`).
- [x] Last five generated passwords are kept in session memory only; they are not written to disk.
- [x] Validates length and requires at least two character types.

## Run
Python 3.10+:

```bash
python -m pip install -r requirements.txt
python password_generator.py
```

On Linux, `pyperclip` may require an installed clipboard provider such as `xclip` or `xsel`; on headless systems the app reports that clipboard access is unavailable without losing the generated password.

## Test
```bash
python -m unittest -v
```

## Security and privacy
- Passwords are generated using the cryptographically secure `secrets` module, not `random`.
- Password history exists only in application memory and is not saved to a file or database.
- Clipboard contents may be visible to other applications or clipboard managers. Clear the clipboard after use on shared devices.
- The strength label is an educational heuristic, not a formal password-audit result.
