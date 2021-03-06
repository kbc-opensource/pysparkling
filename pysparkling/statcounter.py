#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# This file is based on the PySpark version which in turn
# was ported from spark/util/StatCounter.scala
import copy
import math

try:
    from numpy import maximum, minimum, sqrt
except ImportError:
    maximum = max
    minimum = min
    sqrt = math.sqrt


class StatCounter:

    def __init__(self, values=None):
        self.n = 0  # Running count of our values
        self.mu = 0.0  # Running mean of our values
        self.m2 = 0.0  # Running variance numerator (sum of (x - mean)^2)
        self.maxValue = float("-inf")
        self.minValue = float("inf")

        if values:
            for v in values:
                self.merge(v)

    # Add a value into this StatCounter, updating the internal statistics.
    def merge(self, value):
        delta = value - self.mu
        self.n += 1
        self.mu += delta / self.n
        self.m2 += delta * (value - self.mu)
        self.maxValue = maximum(self.maxValue, value)
        self.minValue = minimum(self.minValue, value)

        return self

    # Merge another StatCounter into this one, adding up the
    # internal statistics.
    def mergeStats(self, other):
        if other is self:  # reference equality holds
            # Avoid overwriting fields in a weird order
            return self.mergeStats(other.copy())

        if self.n == 0:
            self.mu = other.mu
            self.m2 = other.m2
            self.n = other.n
            self.maxValue = other.maxValue
            self.minValue = other.minValue

        elif other.n != 0:
            delta = other.mu - self.mu
            if other.n * 10 < self.n:
                self.mu = self.mu + (delta * other.n) / (self.n + other.n)
            elif self.n * 10 < other.n:
                self.mu = other.mu - (delta * self.n) / (self.n + other.n)
            else:
                self.mu = ((self.mu * self.n + other.mu * other.n)
                           / (self.n + other.n))

            self.maxValue = maximum(self.maxValue, other.maxValue)
            self.minValue = minimum(self.minValue, other.minValue)

            self.m2 += other.m2 + ((delta * delta * self.n * other.n)
                                   / (self.n + other.n))
            self.n += other.n

        return self

    # Clone this StatCounter
    def copy(self):
        return copy.deepcopy(self)

    def count(self):
        return int(self.n)

    def mean(self):
        return self.mu

    def sum(self):
        return self.n * self.mu

    def min(self):
        return self.minValue

    def max(self):
        return self.maxValue

    # Return the variance of the values.
    def variance(self):
        if self.n == 0:
            return float('nan')

        return self.m2 / self.n

    #
    # Return the sample variance, which corrects for bias in estimating
    # the variance by dividing by N-1 instead of N.
    #
    def sampleVariance(self):
        if self.n <= 1:
            return float('nan')

        return self.m2 / (self.n - 1)

    # Return the standard deviation of the values.
    def stdev(self):
        return sqrt(self.variance())

    #
    # Return the sample standard deviation of the values, which corrects for
    # bias in estimating the variance by dividing by N-1 instead of N.
    #
    def sampleStdev(self):
        return sqrt(self.sampleVariance())

    def __repr__(self):
        return ("(count: %s, mean: %s, stdev: %s, max: %s, min: %s)" %
                (self.count(), self.mean(), self.stdev(), self.max(), self.min()))
