#!/usr/bin/env python
import torch
from torch import nn
import math

class BasicBlock(nn.Module):
    expansion = 1
    def __init__(self, in_channels, channels, stride=1, dilation=1):
        super(BasicBlock, self).__init__()
        self.stride = stride
        self.dilation = dilation
        if stride > 1 or dilation > 1:
            self.downsample = nn.Conv2d(in_channels, channels, kernel_size=1, stride=stride, bias=False)
            self.bn0 = nn.BatchNorm2d(channels)
            self.conv1 = nn.Conv2d(in_channels, channels, kernel_size=(3,3), stride=stride, dilation=dilation, padding=dilation, bias=False)
        else:
            self.conv1 = nn.Conv2d(in_channels, channels, kernel_size=(3,3), stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=(3,3), stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        residual = x
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)

        x = self.conv2(x)
        x = self.bn2(x)

        if self.stride > 1 or self.dilation > 1:
            residual = self.downsample(residual)
            residual = self.bn0(residual)
        x += residual
        x = self.relu(x)

        return x


class Bottleneck(nn.Module):
    expansion = 4
    def __init__(self, in_channels, channels, stride=1, dilation=1):
        super(Bottleneck, self).__init__()
        self.stride = stride
        self.dilation = dilation
        if stride > 1:
            self.downsample = nn.Conv2d(in_channels, channels*self.expansion, kernel_size=1, stride=stride, bias=False)
            self.bn0 = nn.BatchNorm2d(channels*self.expansion)
        elif in_channels != channels*self.expansion:
            self.downsample = nn.Conv2d(in_channels, channels*self.expansion, kernel_size=1, stride=1, bias=False)
            self.bn0 = nn.BatchNorm2d(channels*self.expansion)
        else:
            self.downsample = None
        self.conv1 = nn.Conv2d(in_channels, channels, kernel_size=(1,1), stride=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.relu = nn.ReLU()
        if stride > 1 or dilation > 1:
            self.conv2 = nn.Conv2d(channels, channels, kernel_size=(3,3), stride=stride, padding=dilation, dilation=dilation, bias=False)
        else:
            self.conv2 = nn.Conv2d(channels, channels, kernel_size=(3,3), stride=1, padding=1, dilation=dilation, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)
        self.conv3 = nn.Conv2d(channels, channels*self.expansion, kernel_size=(1,1), stride=1, bias=False)
        self.bn3 = nn.BatchNorm2d(channels*self.expansion)

    def forward(self, x):
        residual = x
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)

        x = self.conv2(x)
        x = self.bn2(x)
        x = self.relu(x)

        x = self.conv3(x)
        x = self.bn3(x)

        if self.downsample:
            residual = self.downsample(residual)

        x += residual
        x = self.relu(x)

        return x



class ResNet(nn.Module):
    def __init__(self, block, layers, in_channels=3, num_classes=64, dropout=0.0, n_clinical=None):
        super(ResNet, self).__init__()
        self.expansion = 4
        self.factor = 2
        self.conv1 = nn.Conv2d(in_channels, 64, kernel_size=(7,7), stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool2d(kernel_size=(3,3), stride=2, dilation=1, padding=1)
        self.n_clinical = n_clinical

        self.in_channels = 64
        self.strides = [1, 2, 2, 2]
        self.dilations = [1, 1, 1, 1]
        #self.strides = [1, 2, 1, 1]
        #self.dilations = [1, 1, 2, 4]
        self.channels = [64, 128, 256, 512]
        #self.nblocks = [3, 4, 6, 3] -> layers
        self.layers = layers

        self.blocks = []

        for idx, (ch, n_blocks, stride, dilation) in enumerate(zip(self.channels, self.layers, self.strides, self.dilations)):
            blocks = self._make_layer(block, ch, n_blocks, stride=stride, dilation=dilation)
            self.blocks.append(nn.ModuleList(blocks))
        self.blocks = nn.ModuleList(self.blocks)
    
        self.avgpool = nn.AdaptiveAvgPool2d((1,1))

        if self.n_clinical is not None:
            self.classify = nn.Linear(self.channels[-1]*self.expansion + n_clinical, num_classes)
        else:
            self.classify = nn.Linear(self.channels[-1]*self.expansion, num_classes)

        self.dropout = nn.Dropout(dropout)

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2./n))
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()



    def _make_layer(self, block, channels, n_blocks, stride=1, dilation=1):

        layers = []
        layers.append(block(self.in_channels, channels, stride=stride, dilation=dilation))
        self.in_channels = channels * block.expansion
        for i in range(1, n_blocks):
            layers.append(block(self.in_channels, channels))

        return layers



    def forward(self, x, clinical=None, policy=None):
        t = 0

        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.pool(x)


        for segment, n_blocks in enumerate(self.layers):
            for b in range(n_blocks):
                output = self.blocks[segment][b](x)
                x = output
                x = self.dropout(x)
                t += 1

        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        if self.n_clinical is not None:
            x = torch.cat((x, clinical), 1)
            x = self.classify(x)
            x = x.squeeze()
        else:
            x = self.classify(x)

        return x


def resnet50(num_classes=1, in_channels=3, dropout=0.0, blocks=Bottleneck, n_clinical=None):
    return ResNet(blocks, [3,4,6,3], in_channels=in_channels, num_classes=num_classes, dropout=dropout, n_clinical=n_clinical)

def resnet101(num_classes=1, in_channels=3, dropout=0.0, blocks=Bottleneck, n_clinical=None):
    return ResNet(blocks, [3,4,23,3], in_channels=in_channels, num_classes=num_classes, dropout=dropout, n_clinical=n_clinical)

def resnet152(num_classes=1, in_channels=3, dropout=0.0, blocks=Bottleneck, n_clinical=None):
    return ResNet(blocks, [3,8,36,3], in_channels=in_channels, num_classes=num_classes, dropout=dropout, n_clinical=n_clinical)
def resnet200(num_classes=1, in_channels=3, dropout=0.0, blocks=Bottleneck, n_clinical=None):
    return ResNet(blocks, [3,24,36,3], in_channels=in_channels, num_classes=num_classes, dropout=dropout, n_clinical=n_clinical)
