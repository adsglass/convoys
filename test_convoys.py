import datetime
import matplotlib
import numpy
import random
import scipy.stats
matplotlib.use('Agg')  # Needed for matplotlib to run in Travis
import convoys


def test_exponential_model(c=0.05, lambd=0.1, n=100000):
    # With a really long observation window, the rate should converge to the measured
    C = numpy.array([random.random() < c and scipy.stats.expon.rvs(scale=1.0/lambd) or 0.0 for x in range(n)])
    N = numpy.array([100 for converted_at in C])
    B = numpy.array([bool(converted_at > 0) for converted_at in C])
    c = numpy.mean(B)
    model = convoys.Exponential()
    model.fit(C, N, B)
    assert 0.95*c < model.params['c'] < 1.05*c
    assert 0.95*lambd < model.params['lambd'] < 1.05*lambd


def test_gamma_model(c=0.05, lambd=0.1, k=10.0, n=100000):
    C = numpy.array([random.random() < c and scipy.stats.gamma.rvs(a=k, scale=1.0/lambd) or 0.0 for x in range(n)])
    N = numpy.array([1000 for converted_at in C])
    B = numpy.array([bool(converted_at > 0) for converted_at in C])
    c = numpy.mean(B)
    model = convoys.Gamma()
    model.fit(C, N, B)
    assert 0.95*c < model.params['c'] < 1.05*c
    assert 0.95*lambd < model.params['lambd'] < 1.05*lambd
    assert 0.95*k < model.params['k'] < 1.05*k


def test_weibull_model(c=0.05, lambd=0.1, k=0.5, n=100000):
    def sample_weibull():
        # scipy.stats is garbage for this
        # exp(-(x * lambda)^k) = y
        return (-numpy.log(random.random())) ** (1.0/k) / lambd
    B = numpy.array([bool(random.random() < c) for x in range(n)])
    C = numpy.array([b and sample_weibull() or 1.0 for b in B])
    N = numpy.array([1000 for b in B])
    c = numpy.mean(B)
    model = convoys.Weibull()
    model.fit(C, N, B)
    assert 0.95*c < model.params['c'] < 1.05*c
    assert 0.95*lambd < model.params['lambd'] < 1.05*lambd
    assert 0.95*k < model.params['k'] < 1.05*k


def test_bootstrapped_exponential_model(c=0.05, lambd=0.1, n=10000):
    C = numpy.array([random.random() < c and scipy.stats.expon.rvs(scale=1.0/lambd) or 0.0 for x in range(n)])
    N = numpy.array([100 for converted_at in C])
    B = numpy.array([bool(converted_at > 0) for converted_at in C])
    c = numpy.mean(B)
    model = convoys.Bootstrapper('exponential')
    model.fit(C, N, B)
    y, y_lo, y_hi = model.predict_final(confidence_interval=True)
    c_lo = scipy.stats.beta.ppf(0.05, n*c, n*(1-c))
    c_hi = scipy.stats.beta.ppf(0.95, n*c, n*(1-c))
    assert 0.95*c < y < 1.05 * c
    assert 0.95*c_lo < y_lo < 1.05 * c_lo
    assert 0.95*c_hi < y_hi < 1.05 * c_hi


def _get_data(c=0.05, k=10, lambd=0.1, n=1000):
    data = []
    now = datetime.datetime(2000, 7, 1)
    for x in range(n):
        date_a = datetime.datetime(2000, 1, 1) + datetime.timedelta(days=random.random()*100)
        if random.random() < c:
            delay = scipy.stats.gamma.rvs(a=k, scale=1.0/lambd)
            date_b = date_a + datetime.timedelta(days=delay)
            if date_b < now:
                data.append(('foo', date_a, date_b, now))
            else:
                data.append(('foo', date_a, None, now))
        else:
            data.append(('foo', date_a, None, now))
    return data


def test_plot_cohorts():
    convoys.plot_cohorts(_get_data(), projection='gamma')


def test_plot_conversion():
    convoys.plot_timeseries(_get_data(), window=datetime.timedelta(days=7), projection='gamma')


def test_plot_cohorts_share_params():
    convoys.plot_cohorts(_get_data(), projection='gamma', share_params=['k'])
