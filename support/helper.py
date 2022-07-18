from operator import mul
import numpy as np


def dot_product(l1, l2):
    return sum(map(mul, l1, l2))


def head_tail_list(lst):
    return lst[0], lst[-1]


def aggregate_currencies(ccy1, ccy2, fiats):
    ccy1 = {k:v[1] for (k, v) in ccy1.items()}
    ccy2 = {k: 1 for (k, v) in ccy2.items()
            if v == 0.01 or k in fiats}

    ccy1.update(ccy2)
    ccy1 = list(ccy1.keys())
    return ccy1


def immutable_array(arr):
    arr.flags.writeable = False
    return arr


def build_2d_matrix(size, scalars):
    '''
    build a simple 2D scoring matrix.
    Matrix axes growth rate is defined by a log in base 10 function
    '''
    matrix = np.zeros(size)
    scalars = [1/n for n in scalars]

    for m in range(matrix.shape[0]):
        for n in range(matrix.shape[1]):
            matrix[m][n] = round(scalars[0]*np.log10(m+1) +
                                 scalars[1]*np.log10(n+1), 2)
    return matrix


def build_normalized_matrix(size, scalar):
    '''
    build a normalized 2D scoring matrix.
    Matrix axes growth rate is defined by a natural logarithm function
    '''
    m = np.zeros(size)
    # evaluate the bottom right element in the matrix and use it to normalize the matrix
    extrema = round(scalar[0]*np.log(m.shape[0])\
                    +scalar[1]*np.log(m.shape[1]), 2) 

    for a in range(m.shape[0]):
        for b in range(m.shape[1]):
            m[a][b] = round((scalar[0]*np.log(a+1)\
                            +scalar[1]*np.log(b+1))/extrema, 2) 
    return m


def plaid_params(params, score_range):

    due_date = immutable_array(
        np.array(params['metrics']['due_date']))
    duration = immutable_array(
        np.array(params['metrics']['duration']))
    count_zero = immutable_array(
        np.array(params['metrics']['count_zero']))
    count_invest = immutable_array(
        np.array(params['metrics']['count_invest']))
    volume_credit = immutable_array(
        np.array(params['metrics']['volume_credit'])*1000)
    volume_invest = immutable_array(
        np.array(params['metrics']['volume_invest'])*1000)
    volume_balance = immutable_array(
        np.array(params['metrics']['volume_balance'])*1000)
    flow_ratio = immutable_array(
        np.array(params['metrics']['flow_ratio']))
    slope = immutable_array(
        np.array(params['metrics']['slope']))
    slope_lr = immutable_array(
        np.array(params['metrics']['slope_lr']))
    activity_vol_mtx = immutable_array(build_2d_matrix(
        tuple(params['matrices']['activity_volume']['shape']),
        tuple(params['matrices']['activity_volume']['scalars'])
    ))
    activity_cns_mtx = immutable_array(build_2d_matrix(
        tuple(params['matrices']['activity_consistency']['shape']),
        tuple(params['matrices']['activity_consistency']['scalars'])
    ))
    credit_mix_mtx = immutable_array(build_2d_matrix(
        tuple(params['matrices']['credit_mix']['shape']),
        tuple(params['matrices']['credit_mix']['scalars'])
    ))
    diversity_velo_mtx = immutable_array(build_2d_matrix(
        tuple(params['matrices']['diversity_velocity']['shape']),
        tuple(params['matrices']['diversity_velocity']['scalars'])
    ))

    head, tail = head_tail_list(score_range)
    fico = (np.array(score_range[:-1])-head) / (tail-head)
    fico_medians = [round(fico[i]+(fico[i+1]-fico[i]) / 2, 2)
                    for i in range(len(fico)-1)]
    fico_medians.append(1)
    fico_medians = immutable_array(np.array(fico_medians))

    count_lively = immutable_array(
        np.array([round(x, 0) for x in fico*25])[1:])
    count_txn = immutable_array(
        np.array([round(x, 0) for x in fico*40])[1:])
    volume_flow = immutable_array(
        np.array([round(x, 0) for x in fico*1500])[1:])
    volume_withdraw = immutable_array(
        np.array([round(x, 0) for x in fico*1500])[1:])
    volume_deposit = immutable_array(
        np.array([round(x, 0) for x in fico*7000])[1:])
    volume_min = immutable_array(
        np.array([round(x, 0) for x in fico*10000])[1:])
    credit_util_pct = immutable_array(
        np.array([round(x, 2) for x in reversed(fico*0.9)][:-1]))
    frequency_interest = immutable_array(
        np.array([round(x, 2) for x in reversed(fico*0.6)][:-1]))

    r = [due_date, duration, count_zero, count_invest, volume_credit, volume_invest, volume_balance, flow_ratio, slope, slope_lr, activity_vol_mtx, activity_cns_mtx,
         credit_mix_mtx, diversity_velo_mtx, fico_medians, count_lively, count_txn, volume_flow, volume_withdraw, volume_deposit, volume_min, credit_util_pct, frequency_interest]
    return r


def coinbase_params(params, score_range):

    due_date = immutable_array(
        np.array(params['metrics']['due_date']))
    duration = immutable_array(
        np.array(params['metrics']['duration']))
    volume_balance = immutable_array(
        np.array(params['metrics']['volume_balance'])*1000)
    volume_profit = immutable_array(
        np.array(params['metrics']['volume_profit'])*1000)
    count_txn = immutable_array(
        np.array(params['metrics']['count_txn']))
    activity_vol_mtx = immutable_array(build_2d_matrix(
        tuple(params['matrices']['activity_volume']['shape']),
        tuple(params['matrices']['activity_volume']['scalars'])
    ))
    activity_cns_mtx = immutable_array(build_2d_matrix(
        tuple(params['matrices']['activity_consistency']['shape']),
        tuple(params['matrices']['activity_consistency']['scalars'])
    ))

    head, tail = head_tail_list(score_range)
    fico = (np.array(score_range[:-1])-head) / (tail-head)
    fico_medians = [round(fico[i]+(fico[i+1]-fico[i]) / 2, 2)
                    for i in range(len(fico)-1)]
    fico_medians.append(1)
    fico_medians = immutable_array(np.array(fico_medians))

    r = [due_date, duration, volume_balance, volume_profit,
         count_txn, activity_vol_mtx, activity_cns_mtx, fico_medians]
    return r


def covalent_params(params, score_range):

    count_to_four = immutable_array(
        np.array(params['metrics']['count_to_four']))
    volume_now = immutable_array(
        np.array(params['metrics']['volume_now'])*1000) #should be *1000
    volume_per_txn = immutable_array(
        np.array(params['metrics']['volume_per_txn'])*100) #should be *100
    duration = immutable_array(
        np.array(params['metrics']['duration']))
    count_operations = immutable_array(
        np.array(params['metrics']['count_operations']))
    cred_deb = immutable_array(
        np.array(params['metrics']['cred_deb'])*100) #should be *1000
    frequency_txn = immutable_array(
        np.array(params['metrics']['frequency_txn']))
    avg_run_bal = immutable_array(
        np.array(params['metrics']['avg_run_bal'])*100) #should be *100
    due_date = immutable_array(
        np.array(params['metrics']['due_date']))

    mtx_traffic = immutable_array(build_normalized_matrix(
        tuple(params['matrices']['mtx_traffic']['shape']),
        tuple(params['matrices']['mtx_traffic']['scalars'])
    ))
    mtx_stamina = immutable_array(build_normalized_matrix(
        tuple(params['matrices']['mtx_stamina']['shape']),
        tuple(params['matrices']['mtx_stamina']['scalars'])
    ))

    head, tail = head_tail_list(score_range)
    fico = (np.array(score_range[:-1])-head) / (tail-head)
    fico_medians = [round(fico[i]+(fico[i+1]-fico[i]) / 2, 2)
                    for i in range(len(fico)-1)]
    fico_medians.append(1)
    fico_medians = immutable_array(np.array(fico_medians))


    k = ['count_to_four', 'volume_now', 'volume_per_txn', 'duration', 'count_operations', 'cred_deb',
        'frequency_txn', 'avg_run_bal', 'due_date', 'fico_medians', 'mtx_traffic', 'mtx_stamina']

    v = [count_to_four, volume_now, volume_per_txn, duration, count_operations, cred_deb,
        frequency_txn, avg_run_bal, due_date, fico_medians, mtx_traffic, mtx_stamina]

    return dict(zip(k,v))