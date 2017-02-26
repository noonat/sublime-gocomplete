# Sublime Gocomplete

This Sublime Text 3 package adds support for code completions and function
signatures using gocode and gogetdoc. It cooperates with Sublime Text's
autocompletion system.

## Dependencies

Before you can use this, you'll need to install gocode and gogetdoc:

```
go get -u github.com/nsf/gocode
go get -u github.com/zmb3/gogetdoc
```

This package also uses [golangconfig] to discover paths and environment
variables related to Golang. It is installed automatically for you when you
install this package via Package Control.

[golangconfig]: http://github.com/golang/sublime-config

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
