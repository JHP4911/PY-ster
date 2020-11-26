import inspect
import os
import sys
import traceback
import pprint

from ..common import indent, ConfigObject, is_primitive


class RuntimeParser(object):

    def __init__(self, target: str, config: ConfigObject, path=None):
        self._caller = inspect.stack()[1][1]
        self.target = target
        self._file_names = set(map(os.path.normpath, list(map(self._get_file, [target]))))
        self.path = os.path.abspath(path) if path else None
        self.config = config

    def _get_file(self, target):
        file = "Unknown File"
        try:
            if hasattr(target, "__file__"):
                file = target.__file__
            else:
                file = inspect.getfile(target)
        except:
            pass
        return file

    def _handle_call(self, code, locals_dict, args, caller=None):
        print(code.co_name)
        print(args)
        func_name = code.co_name
        params = list(code.co_varnames)[:code.co_argcount]
        args_dict = dict((p,locals_dict[p]) for p in params)
        args_type = { k: str(type(v)).split("'")[1] for k, v in args_dict.items()}
        print(args_type)
        print()

        class_name = type(args_dict['self']).__name__ if 'self' in args_dict else ""
        if not class_name:
            return
        class_name_short = class_name.split('.')[-1]
        module_name = self.target
        for index, value in enumerate(args_dict.values()):
            if index == 0:
                continue
            self.config.add_type_override([module_name, class_name_short, func_name, index, value])

    def _handle_exception(self, code, locals_dict, args, caller=None):
        pass

    def _handle_line(self, code, locals_dict, args, caller=None):
        pass

    def _handle_return(self, code, locals_dict, args, caller=None):
        pass

    def _trace(self, frame, event, args):
        handler = getattr(self, '_handle_' + event)
        event_file = frame.f_code.co_filename
       # if event_file in self._file_names:
        handler(frame.f_code, frame.f_locals, args)
        return self._trace

    def parse(self):
        if self.path:
            path, filename = os.path.split(self.path)
            sys.path.insert(0, path)
            user_module = __import__(filename.split('.')[0])
            sys.settrace(self._trace)
            user_module.main()
            sys.settrace(None)
            