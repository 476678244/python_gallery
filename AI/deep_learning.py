# 虚构目标函数
def o(x, y):
    return 1.0 if x*x + y*y < 1 else 0.0

# 生成数据集
sample_density = 10
xs = [
    [-2.0 + 4 * x/sample_density, -2.0 + 4 * y/sample_density]
    for x in range(sample_density+1)
    for y in range(sample_density+1)
]
dataset = [
    (x, y, o(x, y))
    for x, y in xs
]

# 激活函数
import math

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

# 神经元

from random import seed, random

seed(0)

class Neuron:
    def __init__(self, num_inputs):
        self.weights = [random()-0.5 for _ in range(num_inputs)]
        self.bias = 0.0

    def forward(self, inputs):
        # z = wx + b
        z = sum([
            i * w
            for i, w in zip(inputs, self.weights)
        ]) + self.bias
        return sigmoid(z)

# 神经网络
class MyNet:
    def __init__(self, num_inputs, hidden_shapes):
        layer_shapes = hidden_shapes + [1]
        input_shapes = [num_inputs] + hidden_shapes
        self.layers = [
            [
                Neuron(pre_layer_size)
                for _ in range(layer_size)
            ]
            for layer_size, pre_layer_size in zip(layer_shapes, input_shapes)
        ]

    def forward(self, inputs):
        for layer in self.layers:
            inputs = [
                neuron.forward(inputs)
                for neuron in layer
            ]
        # return the output of the last neuron
        return inputs[0]


net = MyNet(2, [4])
print(net.forward([0, 0]))

# 损失函数
def square_loss(predict, target):
    return (predict-target)**2

# 计算梯度

# 定义导函数：
def sigmoid_derivative(x):
    _output = sigmoid(x)
    return _output * (1 - _output)

def square_loss_derivative(predict, target):
    return 2 * (predict-target)

# 求偏导数
class Neuron:
    ...

    def forward(self, inputs):
        self.inputs_cache = inputs

        # z = wx + b
        self.z_cache = sum([
            i * w
            for i, w in zip(inputs, self.weights)
        ]) + self.bias
        return sigmoid(self.z_cache)

    def zero_grad(self):
        self.d_weights = [0.0 for w in self.weights]
        self.d_bias = 0.0

    def backward(self, d_a):
        d_loss_z = d_a * sigmoid_derivative(self.z_cache)
        self.d_bias += d_loss_z
        for i in range(len(self.inputs_cache)):
            self.d_weights[i] += d_loss_z * self.inputs_cache[i]
        return [d_loss_z * w for w in self.weights]

class MyNet:

    def zero_grad(self):
        for layer in self.layers:
            for neuron in layer:
                neuron.zero_grad()

    def backward(self, d_loss):
        d_as = [d_loss]
        for layer in reversed(self.layers):
            da_list = [
                neuron.backward(d_a)
                for neuron, d_a in zip(layer, d_as)
            ]
            d_as = [sum(da) for da in zip(*da_list)]
