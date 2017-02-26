from __future__ import print_function

import json
import platform
import subprocess
import threading
from collections import defaultdict

import sublime
import sublime_plugin

import golangconfig


OPTIONAL_VARS = [
    'GO386',
    'GOARCH',
    'GOARM',
    'GOBIN',
    'GOHOSTOS',
    'GOHOSTARCH',
    'GOOS',
    'GORACE',
    'GOROOT',
    'GOROOT_FINAL',
]
REQUIRED_VARS = ['GOPATH']

SIGNATURE_TEMPLATE = """
<style>
.decl {{
    font-weight: bold;
}}
.doc {{
    font-family: sans-serif;
    margin-top: 5px;
}}
</style>
<div class="decl">{}</div>
<div class="doc">{}</div>
"""

is_windows = platform.system() == 'Windows'
startup_info = None
if is_windows:
    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW

settings = None


def plugin_loaded():
    global settings
    settings = sublime.load_settings('Gocode.sublime-settings')


class GoCommand(object):

    _views_subprocess_info = defaultdict(dict)

    def __init__(self, name, view):
        self.name = name
        self.view = view
        self.path, self.env = GoCommand.subprocess_info(
            self.name, self.view)

    def run(self, args, stdin):
        """Run the command.

        :param list(str) args: Arguments to pass to the process.
        :param str stdin: Text to use for stdin on the process.
        :returns: (str, str, int) Returns the stdout, stderr, and return code
            of the process.
        """
        proc = subprocess.Popen(
            [self.path] + args, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
            stdout=subprocess.PIPE, env=self.env, startupinfo=startup_info)
        if isinstance(stdin, str):
            stdin = stdin.encode()
        stdout, stderr = proc.communicate(stdin)
        if not isinstance(stdout, str):
            stdout = stdout.decode('utf-8')
        if not isinstance(stderr, str):
            stderr = stderr.decode('utf-8')
        return stdout, stderr, proc.returncode

    @classmethod
    def subprocess_info(cls, name, view):
        """Query the subprocess info for a given go command.

        :param str name: Name of the command.
        :param sublime.View view: Current editor view.
        :returns: (str, dict(str, str)) Returns the path to the executable
            and a dictionary of environment variables that should be passed
            to the process when run.
        :raises RuntimeError: if called from a non-main thread.
        """

        view_subprocess_info = cls._views_subprocess_info[view.id()]
        subprocess_info = view_subprocess_info.get(name)
        if subprocess_info is not None:
            return subprocess_info
        if not is_main_thread():
            # golangconfig requires that settings only be accessed from the
            # main thread, so we can't do anything at this point.
            raise RuntimeError(
                'subprocess_info for {} is not cached, and cannot be created'
                '(because this is not the main thread)'.format(name))
        subprocess_info = golangconfig.subprocess_info(
            name, REQUIRED_VARS, OPTIONAL_VARS, view, view.window())
        view_subprocess_info[name] = subprocess_info
        return subprocess_info


def is_go_source(view, point=None):
    """Return True if the given view contains Go source code.

    :param sublime.View view: View containing the code to be formatted.
    :returns: bool
    """
    if point is None:
        point = view.sel()[0].begin()
    return view.score_selector(point, 'source.go') > 0


def is_main_thread():
    """Return True if the current thread is the main thread.

    :returns bool:
    """
    return isinstance(threading.current_thread(), threading._MainThread)


def get_completions(view, point):
    if not settings.get('show_completions', True):
        return
    stdin = view.substr(sublime.Region(0, view.size()))
    stdout, stderr, return_code = GoCommand('gocode', view).run(
        ['-f=json', 'autocomplete', str(point)], stdin)
    if return_code != 0:
        return
    results = json.loads(stdout)
    if not results:
        return
    completions = [('{}\t{}'.format(r['name'], r['type']), r['name'])
                   for r in results[1]]
    return (completions, sublime.INHIBIT_WORD_COMPLETIONS)


def show_signature(view, point, flags):
    filename = view.file_name()
    pos = '{filename}:#{point}'.format(filename=filename, point=point)
    buf = view.substr(sublime.Region(0, view.size()))
    stdin = '{}\n{}\n{}'.format(filename, view.size(), buf)
    stdout, stderr, return_code = GoCommand('gogetdoc', view).run(
        ['-u', '-json', '-modified', '-pos', pos], stdin)
    if return_code != 0:
        return
    results = json.loads(stdout)
    html = SIGNATURE_TEMPLATE.format(
        results['decl'], results['doc'].split('\n\n')[0].replace('\n', ' '))
    view.show_popup(html, flags=flags, location=point, max_width=600)


class GocodeListener(sublime_plugin.EventListener):

    def __init__(self, *args, **kwargs):
        super(GocodeListener, self).__init__(*args, **kwargs)
        self.paren_pressed_point = None

    def on_query_completions(self, view, prefix, locations):
        point = view.sel()[0].begin()
        if not is_go_source(view, point):
            return
        return get_completions(view, point)

    def on_query_context(self, view, key, operator, operand, match_all):
        if not is_go_source(view):
            return
        if key == 'paren_pressed':
            # Record what point at which the opening paren was pressed, so we
            # can use it later to look for the signature documentation.
            self.paren_pressed_point = view.sel()[0].begin() - 1
            return False

    def on_selection_modified(self, view):
        if not is_go_source(view):
            return
        # Call this here to cache ahead of time, because it can't be called
        # from within the async handler (since that runs on another thread).
        GoCommand.subprocess_info('gogetdoc', view)

    def on_selection_modified_async(self, view):
        if (not is_go_source(view) or
                not settings.get('show_signatures_paren', True)):
            return
        point = self.paren_pressed_point
        self.paren_pressed_point = None
        if point is not None:
            show_signature(view, point, sublime.COOPERATE_WITH_AUTO_COMPLETE)

    def on_hover(self, view, point, hover_zone):
        if (hover_zone != sublime.HOVER_TEXT or not is_go_source(view) or
                not settings.get('show_signatures_hover', True)):
            return
        show_signature(view, point, sublime.HIDE_ON_MOUSE_MOVE_AWAY)
