import torch
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Agg')  # or 'inline'


def norm_metrics(running, norm):
    try:
        running["accuracy"] /= norm
        # running["confusion_matrix"] = running["confusion_matrix"].float() / running["confusion_matrix"].sum()
        running["plastic_debris"]["precision"] /= norm
        running["plastic_debris"]["recall"] /= norm
        running["plastic_debris"]["f1"] /= norm
        running["plastic_debris"]["iou"] /= norm

        running["background"]["precision"] /= norm
        running["background"]["recall"] /= norm
        running["background"]["f1"] /= norm
        running["background"]["iou"] /= norm
        return running
    except KeyError as e:
        raise KeyError(f"invalid key in running metrics dict {e}")



def plot_metrics(running):
    print("accuracy:", running["accuracy"])
    sns.heatmap(running["confusion_matrix"].cpu(), annot=True, cmap="coolwarm")
    plt.show()
    print()
    print("plastic debris metrics")
    print("\t", "precision:", running["plastic_debris"]["precision"])
    print("\t", "recall:", running["plastic_debris"]["recall"])
    print("\t", "f1:", running["plastic_debris"]["f1"])
    print("\t", "iou:", running["plastic_debris"]["iou"])
    print()
    print("background metrics")
    print("\t", "precision:", running["background"]["precision"])
    print("\t", "recall:", running["background"]["recall"])
    print("\t", "f1:", running["background"]["f1"])
    print("\t", "iou:", running["background"]["iou"])


def save_logs(writer, step, y_pred, y_true, loss, mode="train"):
    y_pred = y_pred.view(-1)
    y_true = y_true.view(-1)

    assert y_pred.shape == y_true.shape
    assert torch.all((y_pred == 0) | (y_pred == 1))
    assert torch.all((y_true == 0) | (y_true == 1))

    tp = ((y_pred == 1) & (y_true == 1)).sum().item()
    tn = ((y_pred == 0) & (y_true == 0)).sum().item()
    fp = ((y_pred == 1) & (y_true == 0)).sum().item()
    fn = ((y_pred == 0) & (y_true == 1)).sum().item()

    eps = 1e-8
    acc = tn / (tn + fp + eps)

    pos_precision = tp / (tp + fp + eps)
    pos_recall = tp / (tp + fn + eps)
    pos_f1 = 2 * pos_precision * pos_recall / (pos_precision + pos_recall + eps)
    pos_iou = tp / (tp + fp + fn + eps)

    neg_precision = tn / (tn + fn + eps)
    neg_recall = tn / (tn + fp + eps)
    neg_f1 = 2 * neg_precision * neg_recall / (neg_precision + neg_recall + eps)
    neg_iou = tn / (tn + fp + fn + eps)

    m = {'plastic_debris': {
            'precision': pos_precision,
            'recall': pos_recall,
            'f1': pos_f1,
            'iou': pos_iou
        },
        'background': {
            'precision': neg_precision,
            'recall': neg_recall,
            'f1': neg_f1,
            'iou': neg_iou
        }}

    writer.add_scalar(f"{mode}/loss", loss, step)
    writer.add_scalar(f"{mode}/accuracy", acc, step)
    for cls in ["plastic_debris", "background"]:
        for key in m[cls]:
            writer.add_scalar(f"{mode}/{cls}_{key}", m[cls][key], step)


def update_metrics(running, y_pred, y_true):
    y_pred = y_pred.view(-1)
    y_true = y_true.view(-1)

    assert y_pred.shape == y_true.shape
    assert torch.all((y_pred == 0) | (y_pred == 1))
    assert torch.all((y_true == 0) | (y_true == 1))

    tp = ((y_pred == 1) & (y_true == 1)).sum().item()
    tn = ((y_pred == 0) & (y_true == 0)).sum().item()
    fp = ((y_pred == 1) & (y_true == 0)).sum().item()
    fn = ((y_pred == 0) & (y_true == 1)).sum().item()

    eps = 1e-8
    acc = tn / (tn + fp + eps)

    pos_precision = tp / (tp + fp + eps)
    pos_recall = tp / (tp + fn + eps)
    pos_f1 = 2 * pos_precision * pos_recall / (pos_precision + pos_recall + eps)
    pos_iou = tp / (tp + fp + fn + eps)

    neg_precision = tn / (tn + fn + eps)
    neg_recall = tn / (tn + fp + eps)
    neg_f1 = 2 * neg_precision * neg_recall / (neg_precision + neg_recall + eps)
    neg_iou = tn / (tn + fp + fn + eps)

    confusion_matrix = torch.tensor([[tn, fp], [fn, tp]])

    if not running:
        return {
            'accuracy': acc,
            'confusion_matrix': confusion_matrix,
            'plastic_debris': {
                'precision': pos_precision,
                'recall': pos_recall,
                'f1': pos_f1,
                'iou': pos_iou
            },
            'background': {
                'precision': neg_precision,
                'recall': neg_recall,
                'f1': neg_f1,
                'iou': neg_iou
            },
        }
    if isinstance(running, dict):
        try:
            running["accuracy"] += acc
            running["confusion_matrix"] += confusion_matrix
            running["plastic_debris"]["precision"] += pos_precision
            running["plastic_debris"]["recall"] += pos_recall
            running["plastic_debris"]["f1"] += pos_f1
            running["plastic_debris"]["iou"] += pos_iou

            running["background"]["precision"] += neg_precision
            running["background"]["recall"] += neg_recall
            running["background"]["f1"] += neg_f1
            running["background"]["iou"] += neg_iou
            return running
        except KeyError as e:
            raise KeyError(f"invalid key in running metrics dict {e}")
