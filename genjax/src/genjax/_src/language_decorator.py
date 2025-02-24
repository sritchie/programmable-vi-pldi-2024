# Copyright 2022 MIT Probabilistic Computing Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect

from genjax._src.core.datatypes.generative import GenerativeFunction
from genjax._src.core.typing import Callable
from genjax._src.generative_functions.builtin.builtin_gen_fn import (
    BuiltinGenerativeFunction,
)


#####
# Language decorator
#####

# TODO: possibly just shorthand `gen = BuiltinGenerativeFunction.new`
# and defer wrapping into higher combinators via `functools` idioms.


def gen(callable: Callable, **kwargs) -> GenerativeFunction:
    if inspect.isclass(callable) or inspect.ismethod(callable):
        return lambda source: callable(
            BuiltinGenerativeFunction.new(source),
            **kwargs,
        )
    else:
        return BuiltinGenerativeFunction.new(callable)
