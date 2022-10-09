from bayes_opt import BayesianOptimization
import numpy as np
from main import bayesian_optimization

best_using_rate = 0.0

pbounds = {
        'lambda_1': (1, 10),
        'lambda_2': (1, 10),
        'bad_rate': (0.1, 0.5),
        'beta': (1, 1.1),
        'g1': (0, 1),
        'g2': (0, 1),
}

optimizer = BayesianOptimization(
    f=bayesian_optimization,
    pbounds=pbounds
    )

optimizer.maximize(init_points = 20, n_iter = 25, acq = 'ei', xi = 0.0)
print(optimizer.max)
