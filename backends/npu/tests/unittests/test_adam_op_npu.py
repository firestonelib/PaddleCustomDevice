#  Copyright (c) 2021 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

import numpy as np
import paddle
import paddle.fluid as fluid
from tests.op_test import OpTest

paddle.enable_static()
SEED = 2021


def adam_step(inputs, attributes):
    """
    Simulate one step of the adam optimizer
    :param inputs: dict of inputs
    :param attributes: dict of attributes
    :return tuple: tuple of output param, moment1, moment2,
    beta1 power accumulator and beta2 power accumulator
    """
    param = inputs["Param"]
    grad = inputs["Grad"]
    moment1 = inputs["Moment1"]
    moment2 = inputs["Moment2"]
    lr = inputs["LearningRate"]
    beta1_pow = inputs["Beta1Pow"]
    beta2_pow = inputs["Beta2Pow"]

    epsilon = attributes["epsilon"]

    if "beta1" in attributes:
        beta1 = attributes["beta1"]
    else:
        beta1 = inputs["Beta1Tensor"][0]
    if "beta2" in attributes:
        beta2 = attributes["beta2"]
    else:
        beta2 = inputs["Beta2Tensor"][0]

    moment1_out = beta1 * moment1 + (1 - beta1) * grad
    moment2_out = beta2 * moment2 + (1 - beta2) * np.square(grad)
    lr_t = lr * np.sqrt(1 - beta2_pow) / (1 - beta1_pow)
    param_out = param - lr_t * (moment1_out / (np.sqrt(moment2_out) + epsilon))
    return param_out, moment1_out, moment2_out


class TestAdam(OpTest):
    def setUp(self):
        self.set_npu()
        self.place = paddle.CustomPlace("npu", 0)
        self.op_type = "adam"
        param = np.random.uniform(-1, 1, (102, 105)).astype("float32")
        grad = np.random.uniform(-1, 1, (102, 105)).astype("float32")
        moment1 = np.random.uniform(-1, 1, (102, 105)).astype("float32")
        # The second moment is positive
        moment2 = np.random.random((102, 105)).astype("float32")

        learning_rate = 0.004
        beta1 = 0.78
        beta2 = 0.836
        epsilon = 1e-4
        beta1_pow = beta1**10
        beta2_pow = beta2**10

        self.inputs = {
            "Param": param,
            "Grad": grad,
            "Moment1": moment1,
            "Moment2": moment2,
            "LearningRate": np.array([learning_rate]).astype("float32"),
            "Beta1Pow": np.array([beta1_pow]).astype("float32"),
            "Beta2Pow": np.array([beta2_pow]).astype("float32"),
        }

        self.attrs = {"epsilon": epsilon, "beta1": beta1, "beta2": beta2}

        param_out, moment1_out, moment2_out = adam_step(self.inputs, self.attrs)

        self.outputs = {
            "Moment1Out": moment1_out,
            "Moment2Out": moment2_out,
            "ParamOut": param_out,
            "Beta1PowOut": np.array([beta1_pow]).astype("float32") * beta1,
            "Beta2PowOut": np.array([beta2_pow]).astype("float32") * beta2,
        }

    def set_npu(self):
        self.__class__.use_custom_device = True

    def init_dtype(self):
        self.dtype = np.float32

    def test_check_output(self):
        self.check_output_with_place(self.place, atol=1e-5)


class TestAdamWithEpsilonTensor(OpTest):
    def setUp(self):
        self.set_npu()
        self.place = paddle.CustomPlace("npu", 0)
        self.op_type = "adam"
        param = np.random.uniform(-1, 1, (102, 105)).astype("float32")
        grad = np.random.uniform(-1, 1, (102, 105)).astype("float32")
        moment1 = np.random.uniform(-1, 1, (102, 105)).astype("float32")
        # The second moment is positive
        moment2 = np.random.random((102, 105)).astype("float32")

        learning_rate = 0.004
        beta1 = 0.78
        beta2 = 0.836
        epsilon = 1e-4
        beta1_pow = beta1**10
        beta2_pow = beta2**10

        self.inputs = {
            "Param": param,
            "Grad": grad,
            "Moment1": moment1,
            "Moment2": moment2,
            "LearningRate": np.array([learning_rate]).astype("float32"),
            "Beta1Pow": np.array([beta1_pow]).astype("float32"),
            "Beta2Pow": np.array([beta2_pow]).astype("float32"),
            "Beta1Tensor": np.array([beta1]).astype("float32"),
            "Beta2Tensor": np.array([beta2]).astype("float32"),
            "EpsilonTensor": np.array([epsilon]).astype("float32"),
        }

        self.attrs = {"epsilon": epsilon}

        param_out, moment1_out, moment2_out = adam_step(self.inputs, self.attrs)

        self.outputs = {
            "Moment1Out": moment1_out,
            "Moment2Out": moment2_out,
            "ParamOut": param_out,
            "Beta1PowOut": np.array([beta1_pow]).astype("float32") * beta1,
            "Beta2PowOut": np.array([beta2_pow]).astype("float32") * beta2,
        }

    def set_npu(self):
        self.__class__.use_custom_device = True

    def init_dtype(self):
        self.dtype = np.float32

    def test_check_output(self):
        self.check_output_with_place(self.place, atol=1e-5)


@unittest.skip(reason="disable_ut in Paddle CI")
class TestAdamOpWithSkipUpdate(OpTest):
    def setUp(self):
        self.set_npu()
        self.place = paddle.CustomPlace("npu", 0)
        self.op_type = "adam"
        param = np.random.uniform(-1, 1, (102, 105)).astype("float32")
        grad = np.random.uniform(-1, 1, (102, 105)).astype("float32")
        moment1 = np.random.uniform(-1, 1, (102, 105)).astype("float32")
        # The second moment is positive
        moment2 = np.random.random((102, 105)).astype("float32")

        learning_rate = 0.004
        beta1 = 0.78
        beta2 = 0.836
        epsilon = 1e-4
        beta1_pow = beta1**10
        beta2_pow = beta2**10

        self.inputs = {
            "Param": param,
            "Grad": grad,
            "Moment1": moment1,
            "Moment2": moment2,
            "LearningRate": np.array([learning_rate]).astype("float32"),
            "Beta1Pow": np.array([beta1_pow]).astype("float32"),
            "Beta2Pow": np.array([beta2_pow]).astype("float32"),
            "Beta1Tensor": np.array([beta1]).astype("float32"),
            "Beta2Tensor": np.array([beta2]).astype("float32"),
            "EpsilonTensor": np.array([epsilon]).astype("float32"),
            "SkipUpdate": np.array([True]).astype("bool"),
        }

        self.attrs = {"epsilon": epsilon}

        self.outputs = {
            "Moment1Out": moment1,
            "Moment2Out": moment2,
            "ParamOut": param,
            "Beta1PowOut": self.inputs["Beta1Pow"],
            "Beta2PowOut": self.inputs["Beta2Pow"],
        }

    def set_npu(self):
        self.__class__.use_custom_device = True

    def init_dtype(self):
        self.dtype = np.float32

    def test_check_output(self):
        self.check_output_with_place(self.place, atol=1e-5)


class TestAdamOpWithGlobalBetaPow(OpTest):
    def setUp(self):
        self.set_npu()
        self.place = paddle.CustomPlace("npu", 0)
        self.op_type = "adam"
        param = np.random.uniform(-1, 1, (102, 105)).astype("float32")
        grad = np.random.uniform(-1, 1, (102, 105)).astype("float32")
        moment1 = np.random.uniform(-1, 1, (102, 105)).astype("float32")
        # The second moment is positive
        moment2 = np.random.random((102, 105)).astype("float32")

        learning_rate = 0.004
        beta1 = 0.78
        beta2 = 0.836
        epsilon = 1e-4
        beta1_pow = beta1**10
        beta2_pow = beta2**10

        self.inputs = {
            "Param": param,
            "Grad": grad,
            "Moment1": moment1,
            "Moment2": moment2,
            "LearningRate": np.array([learning_rate]).astype("float32"),
            "Beta1Pow": np.array([beta1_pow]).astype("float32"),
            "Beta2Pow": np.array([beta2_pow]).astype("float32"),
            "Beta1Tensor": np.array([beta1]).astype("float32"),
            "Beta2Tensor": np.array([beta2]).astype("float32"),
            "EpsilonTensor": np.array([epsilon]).astype("float32"),
        }

        attributes = {"epsilon": epsilon}

        param_out, moment1_out, moment2_out = adam_step(self.inputs, attributes)

        self.attrs = {"use_global_beta_pow": True}

        # use_global_beta_pow=True, Beta1PowOut and Beta2PowOut are empty.
        self.outputs = {
            "Moment1Out": moment1_out,
            "Moment2Out": moment2_out,
            "ParamOut": param_out,
            "Beta1PowOut": np.array([]),
            "Beta2PowOut": np.array([]),
        }

    def set_npu(self):
        self.__class__.use_custom_device = True

    def init_dtype(self):
        self.dtype = np.float32

    def test_check_output(self):
        self.check_output_with_place(self.place, atol=1e-5)


class TestNet(unittest.TestCase):
    def _test(self, run_npu=True):
        main_prog = paddle.static.Program()
        startup_prog = paddle.static.Program()
        main_prog.random_seed = SEED
        startup_prog.random_seed = SEED
        np.random.seed(SEED)

        a_np = np.random.random(size=(32, 32)).astype("float32")
        b_np = np.random.random(size=(32, 32)).astype("float32")
        label_np = np.random.randint(2, size=(32, 1)).astype("int64")

        with paddle.static.program_guard(main_prog, startup_prog):
            a = paddle.static.data(name="a", shape=[32, 32], dtype="float32")
            b = paddle.static.data(name="b", shape=[32, 32], dtype="float32")
            label = paddle.static.data(name="label", shape=[32, 1], dtype="int64")

            sum = paddle.add(a, b)
            z = paddle.pow(sum, 2.0)

            fc_1 = paddle.static.nn.fc(x=z, size=128)
            prediction = paddle.static.nn.fc(x=fc_1, size=2, activation="softmax")

            cost = paddle.nn.functional.cross_entropy(input=prediction, label=label)
            loss = paddle.mean(cost)
            adam = fluid.optimizer.Adam(learning_rate=0.01)
            adam.minimize(loss)

        if run_npu:
            place = paddle.CustomPlace("npu", 0)
        else:
            place = paddle.CPUPlace()

        exe = paddle.static.Executor(place)
        exe.run(startup_prog)

        print("Start run on {}".format(place))
        for epoch in range(100):

            pred_res, loss_res = exe.run(
                main_prog,
                feed={"a": a_np, "b": b_np, "label": label_np},
                fetch_list=[prediction, loss],
            )
            if epoch % 10 == 0:
                print(
                    "Epoch {} | Prediction[0]: {}, Loss: {}".format(
                        epoch, pred_res[0], loss_res
                    )
                )

        return pred_res, loss_res

    def test_npu(self):
        cpu_pred, cpu_loss = self._test(False)
        npu_pred, npu_loss = self._test(True)

        self.assertTrue(np.allclose(npu_pred, cpu_pred, rtol=1e-3))
        self.assertTrue(np.allclose(npu_loss, cpu_loss, rtol=1e-3))


class TestNetWithEpsilonTensor(unittest.TestCase):
    def _test(
        self,
        place,
        use_tensor=True,
        use_fluid_api=True,
        use_global_beta_pow=False,
        flatten_param_grads=False,
    ):
        paddle.enable_static()
        main_prog = paddle.static.Program()
        startup_prog = paddle.static.Program()
        SEED = 2021
        paddle.seed(SEED)
        np.random.seed(SEED)

        a_np = np.random.random(size=(2, 2)).astype("float32")
        b_np = np.random.random(size=(2, 2)).astype("float32")
        label_np = np.random.randint(2, size=(2, 1)).astype("int64")
        weight_attr1 = paddle.ParamAttr(
            name="weight1",
            initializer=fluid.initializer.Constant(value=1.0),
            trainable=True,
        )
        weight_attr2 = paddle.ParamAttr(
            name="weight2",
            initializer=fluid.initializer.Constant(value=2.0),
            trainable=True,
        )
        clip = paddle.nn.ClipGradByGlobalNorm(clip_norm=1.0)

        with paddle.static.program_guard(main_prog, startup_prog):
            with paddle.utils.unique_name.guard():
                a = paddle.static.data(name="a", shape=[2, 2], dtype="float32")
                b = paddle.static.data(name="b", shape=[2, 2], dtype="float32")
                label = paddle.static.data(name="label", shape=[2, 1], dtype="int64")

                sum = paddle.add(a, b)
                z = paddle.pow(sum, 2.0)

                fc_1 = paddle.static.nn.fc(x=z, size=2, weight_attr=weight_attr1)
                prediction = paddle.static.nn.fc(
                    x=fc_1, size=2, weight_attr=weight_attr2, activation="softmax"
                )

                cost = paddle.nn.functional.cross_entropy(input=prediction, label=label)
                loss = paddle.mean(cost)
                beta1_init = 0.9
                beta2_init = 0.999
                epsilon_init = 1e-8
                if use_tensor:
                    beta1 = paddle.static.create_global_var(
                        shape=[1],
                        value=float(beta1_init),
                        dtype="float32",
                        persistable=True,
                        name="beta1",
                    )
                    beta2 = paddle.static.create_global_var(
                        shape=[1],
                        value=float(beta2_init),
                        dtype="float32",
                        persistable=True,
                        name="beta2",
                    )
                    epsilon = paddle.static.create_global_var(
                        shape=[1],
                        value=float(epsilon_init),
                        dtype="float32",
                        persistable=True,
                        name="epsilon",
                    )
                    if use_fluid_api:
                        adam = fluid.optimizer.Adam(
                            learning_rate=0.01,
                            beta1=beta1,
                            beta2=beta2,
                            epsilon=epsilon,
                            use_global_beta_pow=use_global_beta_pow,
                            flatten_param_grads=flatten_param_grads,
                            align_size=256,
                            grad_clip=clip,
                        )
                    else:
                        adam = paddle.optimizer.Adam(
                            learning_rate=0.01,
                            beta1=beta1,
                            beta2=beta2,
                            epsilon=epsilon,
                            grad_clip=clip,
                        )
                else:
                    if use_fluid_api:
                        adam = fluid.optimizer.Adam(
                            learning_rate=0.01,
                            beta1=beta1_init,
                            beta2=beta2_init,
                            epsilon=epsilon_init,
                            use_global_beta_pow=use_global_beta_pow,
                            flatten_param_grads=flatten_param_grads,
                            align_size=256,
                            grad_clip=clip,
                        )
                    else:
                        adam = fluid.optimizer.Adam(
                            learning_rate=0.01,
                            beta1=beta1_init,
                            beta2=beta2_init,
                            epsilon=epsilon_init,
                            grad_clip=clip,
                        )

                adam.minimize(loss)

        scope = fluid.Scope()
        with fluid.scope_guard(scope):
            exe = paddle.static.Executor(place)
            exe.run(startup_prog)

            print("Start run on {}".format(place))
            for epoch in range(10):
                pred_res, loss_res = exe.run(
                    main_prog,
                    feed={"a": a_np, "b": b_np, "label": label_np},
                    fetch_list=[prediction, loss],
                )
                print(
                    "Epoch {} | Prediction[0]: {}, Loss: {}".format(
                        epoch, pred_res[0], loss_res
                    )
                )
            paddle.disable_static()
            return pred_res, loss_res

    def _test_with_place(self, place):
        preds = []
        losses = []

        for use_tensor in [True, False]:
            for use_fluid_api in [True, False]:
                for use_global_beta_pow in [True, False]:
                    for flatten_param_grads in [True, False]:
                        pred, loss = self._test(
                            place,
                            use_tensor,
                            use_fluid_api,
                            use_global_beta_pow,
                            flatten_param_grads,
                        )
                        preds.append(pred)
                        losses.append(loss)
        for pred in preds:
            print("pred: ", pred)
            print("preds[0]: ", preds[0])
            self.assertTrue(np.allclose(pred, preds[0]))
        for loss in losses:
            self.assertTrue(np.allclose(loss, losses[0]))

    def test_adam_api(self):
        # NOTE(zhiqiu): cpu and gpu has different seed, so should compare separatly.
        self._test_with_place(paddle.CPUPlace())
        self._test_with_place(paddle.CustomPlace("npu", 0))


if __name__ == "__main__":
    unittest.main()
