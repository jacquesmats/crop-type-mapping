import os
import json
import pandas as pd
import argparse

def load_run(path):

    result_file = os.path.join(path, "result.json")

    if not os.path.exists(result_file):
        return None

    with open(result_file,'r') as f:
        lines = f.readlines()

    if len(lines) > 0:
        result = json.loads(lines[-1])
        return result["accuracy"], result["loss"], result["training_iteration"], result["timestamp"], result["config"]
    else:
        return None

def load_experiment(path):
    runs = os.listdir(path)

    result = list()
    for run in runs:
        runpath = os.path.join(path, run)

        run = load_run(runpath)
        if run is None:
            continue
        else:
            accuracy, loss, training_iteration, timestamp, config = run

        result.append(
            dict(
                accuracy=accuracy,
                loss=loss,
                training_iteration=training_iteration,
                batchsize=config["batchsize"],
                dataset=config["dataset"],
                hidden_dims=config["hidden_dims"],
                num_rnn_layers=config["num_rnn_layers"],
                learning_rate=config["learning_rate"],
                fold=config["fold"],
                dropout=config["dropout"]
            )
        )

    return result

def parse_experiment(experimentpath, outcsv=None, n=5):
    result = load_experiment(experimentpath)

    if len(result) == 0:
        print("Warning! Experiment {} returned no runs".format(experimentpath))
        return None

    result = pd.DataFrame(result)
    # average accuracy over the same columns (particularily over the fold variable...)
    grouped = result.groupby(["hidden_dims", "learning_rate", "num_rnn_layers"])["accuracy"]
    nfolds = grouped.count().rename("nfolds")
    mean_accuracy = grouped.mean().rename("mean_accuracy")
    std_accuracy = grouped.std().rename("std_accuracy")

    score = pd.concat([mean_accuracy, std_accuracy, nfolds], axis=1)

    top = score.nlargest(n, "mean_accuracy")

    dataset = os.path.basename(experimentpath)
    top.reset_index(inplace=True)
    top["dataset"] = dataset

    if outcsv is not None:
        top.to_csv(outcsv)

    return top

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'experiment', type=str, help='Experiment. Defined as subfolder in ray root directory')
    parser.add_argument(
        '-c','--outcsv', type=str, default=None, help='output path for csv file')
    parser.add_argument(
        '-r','--root', type=str, default=os.path.join(os.environ["HOME"], "ray_results"),
        help='ray root directory. Defaults to $HOME/ray_results')
    parser.add_argument(
        '-k','--top-k', type=int, default=1,
        help='print top K entries (default 1)')
    args, _ = parser.parse_known_args()
    return args

def load_set_of_experiments(path):
    experiments = os.listdir(path)

    best_hyperparams = list()
    for experiment in experiments:

        experimentpath = os.path.join(path,experiment)

        if os.path.isdir(experimentpath):
            print("parsing experiment "+experiment)
            result = parse_experiment(experimentpath=experimentpath, outcsv=None, n=1)
            if result is not None:
                best_hyperparams.append(result)

    summary = pd.concat(best_hyperparams)

    csvfile = os.path.join(path, "hyperparams.csv")
    print("writing "+csvfile)
    summary.to_csv(csvfile)

if __name__=="__main__":

    args = parse_args()

    load_set_of_experiments(args.root)


    experimentpath = os.path.join(args.root, args.experiment)

    result = parse_experiment(experimentpath, outcsv=args.outcsv)

    print(result)



    pass