"""A Kurt plugin for Octopi"""
import kurt
from kurt.plugin import Kurt

# Import the shared functions from the scratch14 plugin
from kurt.scratch14 import Scratch14Plugin, Serializer
from kurt.scratch14.user_objects import user_objects_by_name, UserObjectDef, \
                                        make_user_objects


user_objects_by_name = user_objects_by_name.copy()
user_objects_by_name['ScriptableScratchMorph'] = UserObjectDef(
    None, 'BaseMorph', [('name', None),
                        ('variables', {}),
                        ('scripts', []),
                        ('isClone', False),
                        ('media', []),
                        ('costume', None),
                        ('hidden', []),
                        ])
user_objects_by_name['ScratchStageMorph'] = UserObjectDef(
    6, 'ScriptableScratchMorph',
    user_objects_by_name['ScratchStageMorph'].defaults.copy())
user_objects_by_name['ScratchSpriteMorph'] = UserObjectDef(
    4, 'ScriptableScratchMorph',
    user_objects_by_name['ScratchSpriteMorph'].defaults.copy())


class OctoSerializer(Serializer):
    def load_scriptable(self, kurt_scriptable, v14_scriptable):
        Serializer.load_scriptable(self, kurt_scriptable, v14_scriptable)
        kurt_scriptable.hidden = map(self.load_script, v14_scriptable.hidden)


class OctopiPlugin(Scratch14Plugin):
    name = 'octopi'
    display_name = 'Octopi from Scratch 1.4'
    extension = '.oct'
    user_objects = make_user_objects(user_objects_by_name)
    serializer_cls = OctoSerializer


Kurt.register(OctopiPlugin())
