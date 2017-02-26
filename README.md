# Sublime Gocode

This Sublime Text 3 package adds support for code completions and function
signatures using gocode and godocget. It cooperates with Sublime Text's
autocompletion system.

## Settings

This plugin has the following settings:

```javascript
{
  // Set to false to disable gocode autocompletion.
  "show_completions": true,

  // Set to false to disable signature help when hovering with the mouse.
  "show_signatures_hover": true,

  // Set to false to disable signature help when typing a function call.
  "show_signatures_paren": true
}
```

## Autocomplete on "."

By default, Sublime Text 3 will only autocomplete when you start typing
letters. If you want to autocomplete after pressing `.`, you can open Sublime
Text -> Preferences -> Settings - Syntax Specific (while editing a Go file),
and add this:

```javascript
// User/Preferences.sublime-settings or User/Go.sublime-settings
{
  // ...
  "auto_complete_triggers": [
    {"selector": "source.go", "characters": "."}
  ]
}
```

If you *only* want completion after dot, you can also add this:

```javascript
// User/Preferences.sublime-settings or User/Go.sublime-settings
{
  // ...
  "auto_complete_selector": "-"
}
```
