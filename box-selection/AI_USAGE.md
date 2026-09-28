# AI Usage

> TEMPLATE: fill this in yourself, honestly, from your real process.
> Keep it specific: paste your actual prompts and what you actually decided.

## Tools used
- (e.g. Claude via claude.ai: what you used it for)

## Prompts I gave
1. (paste prompt)
2. (paste prompt)

## Output I accepted
- (e.g. project structure, packing.py approach: and why)

## Output I rejected or modified
- (what you changed and why)

## Mistakes the AI made
- Found during testing: `Box.to_spec()` passed `cost` through unchanged, so a just-created Box
  (cost given as a string) produced a str instead of a Decimal. Caught by `test_models.py`,
  fixed by converting with `Decimal(str(...))`.
- (add anything else you personally noticed)

## How I verified the final code
- (e.g. ran `python manage.py test`, read through packing.py, hand-checked expected boxes in
  test_api.py against the fixture numbers, tried the API with curl)
