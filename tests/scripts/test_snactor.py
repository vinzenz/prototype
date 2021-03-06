import json
import os
from subprocess import check_call, check_output, CalledProcessError

from helpers import repository_dir

import pytest


def setup_module(m):
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


def test_discovery(repository_dir):
    with repository_dir.as_cwd():
        check_call(['snactor', 'discover'])

        # Ensure snactor discover --json returns valid json
        output = check_output(['snactor', 'discover', '--json']).decode('utf-8')
        data = json.loads(output)
        assert 'actors' in data
        assert 'base_dir' in data and repository_dir.samefile(data['base_dir'])
        assert 'models' in data
        assert 'repository' in data
        assert 'tags' in data
        assert 'topics' in data

    with type(repository_dir)(path=repository_dir.dirname).as_cwd():
        with pytest.raises(CalledProcessError):
            check_call(['snactor', 'discover'])


def test_new_tag(repository_dir):
    with repository_dir.as_cwd():
        check_call(['snactor', 'new-tag', 'Test'])
        assert repository_dir.join('tags/test.py').check(file=True)
        check_call(['snactor', 'discover'])


def test_new_topic(repository_dir):
    with repository_dir.as_cwd():
        # We need the topic to be created already for the model
        # So we have to check if it wasn't already created
        if not repository_dir.join('topics/test.py').check(file=True):
            check_call(['snactor', 'new-topic', 'Test'])
        assert repository_dir.join('topics/test.py').check(file=True)
        check_call(['snactor', 'discover'])


def test_new_model(repository_dir):
    # We need the topic to be created already
    if not repository_dir.join('topics/test.py').check(file=True):
        test_new_topic(repository_dir)
    with repository_dir.as_cwd():
        # We need the model to be created already for the actor
        # So we have to check if it wasn't already created
        if not repository_dir.join('models/testmodel.py').check(file=True):
            check_call(['snactor', 'new-model', 'TestModel'])
        assert repository_dir.join('models/testmodel.py').check(file=True)
        with pytest.raises(CalledProcessError):
            # Now discover should fail due to the missing topic
            check_call(['snactor', 'discover'])
        repository_dir.join('models/testmodel.py').write('''
from leapp.models import Model, fields
from leapp.topics import TestTopic


class TestModel(Model):
    topic = TestTopic
    value = fields.String(default='Test value')
''')
        check_call(['snactor', 'discover'])


def test_ref_model(repository_dir):
    # We need the topic to be created already
    if not repository_dir.join('topics/test.py').check(file=True):
        test_new_topic(repository_dir)
    with repository_dir.as_cwd():
        # We need the model to be created already for the actor
        # So we have to check if it wasn't already created
        if not repository_dir.join('models/a.py').check(file=True):
            check_call(['snactor', 'new-model', 'A'])
        assert repository_dir.join('models/a.py').check(file=True)
        with pytest.raises(CalledProcessError):
            # Now discover should fail due to the missing topic
            check_call(['snactor', 'discover'])
        repository_dir.join('models/a.py').write('''
from leapp.models import Model, fields, TestModel
from leapp.topics import TestTopic


class A(Model):
    topic = TestTopic
    referenced = fields.Model(TestModel)
''')
        check_call(['snactor', 'discover'])


def test_new_actor(repository_dir):
    # We need the model to be created already
    if not repository_dir.join('models/testmodel.py').check(file=True):
        test_new_model(repository_dir)
    with repository_dir.as_cwd():
        check_call(['snactor', 'new-actor', 'Test'])
        assert repository_dir.join('actors/test/actor.py').check(file=True)
        with pytest.raises(CalledProcessError):
            check_call(['snactor', 'discover'])
        repository_dir.join('actors/test/actor.py').write('''
from leapp.actors import Actor
from leapp.models import TestModel
from leapp.tags import TestTag

class Test(Actor):
    name = 'test'
    description = 'No description has been provided for the test actor.'
    consumes = ()
    produces = (TestModel,)
    tags = (TestTag.Common,)

    def process(self):
        pass
''')
        check_call(['snactor', 'discover'])


def test_new_workflow(repository_dir):
    if repository_dir.join('workflows/test.py').check(file=True):
        # Test must have been run already
        return
    with repository_dir.as_cwd():
        check_call(['snactor', 'workflow', 'new', 'Test'])
        assert repository_dir.join('workflows/test.py').check(file=True)
        check_call(['snactor', 'discover'])
        content = repository_dir.join('workflows/test.py').read()
        repository_dir.join('workflows/test.py').write('from leapp.tags import TestTag\n' + content + '''

    class TestPhase(Phase):
         name = 'unit-test-workflow-phase'
         filter = TagFilter(TestTag)
         policies = Policies(Policies.Errors.FailPhase,
                             Policies.Retry.Phase)
         flags = Flags()
''')
        check_call(['snactor', 'discover'])


def test_run_workflow(repository_dir):
    # We need the workflow to be created already
    if not repository_dir.join('workflows/test.py').check(file=True):
        test_new_workflow(repository_dir)
    with pytest.raises(CalledProcessError):
        check_call(['snactor', 'workflow', 'run', 'Test'])
    with repository_dir.as_cwd():
        check_call(['snactor', 'workflow', 'run', 'Test'])
        check_call(['snactor', '--debug', 'workflow', 'run', 'Test'])
        check_call(['snactor', 'workflow', '--debug', 'run', 'Test'])
        check_call(['snactor', 'workflow', 'run', '--debug', 'Test'])


def test_run_actor(repository_dir):
    with repository_dir.as_cwd():
        check_call(['snactor', 'run', 'Test'])
        check_call(['snactor', 'run', '--print-output', 'Test'])
        check_call(['snactor', 'run', '--save-output', 'Test'])
        check_call(['snactor', 'run', '--print-output', '--save-output', 'Test'])
        check_call(['snactor', 'run', '--debug', 'Test'])
        check_call(['snactor', 'run', '--debug', '--print-output', 'Test'])
        check_call(['snactor', 'run', '--debug', '--save-output', 'Test'])
        check_call(['snactor', 'run', '--debug', '--print-output', '--save-output', 'Test'])
        check_call(['snactor', '--debug', 'run', 'Test'])
        check_call(['snactor', '--debug', 'run', '--print-output', 'Test'])
        check_call(['snactor', '--debug', 'run', '--save-output', 'Test'])
        check_call(['snactor', '--debug', 'run', '--print-output', '--save-output', 'Test'])


def test_clear_messages(repository_dir):
    with repository_dir.as_cwd():
        check_call(['snactor', 'messages', 'clear'])
