import torch


class AverageMeter(object):
    """Taken from https://github.com/pytorch/examples/blob/master/imagenet/main.py"""
    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


def accuracy(preds, targets, k):
    batch_size = targets.size(0)
    _, pred = preds.topk(k, 1, True, True)
    correct = pred.eq(targets.view(-1, 1).expand_as(pred))
    correct_total = correct.view(-1).float().sum()
    return correct_total.item() * (100.0 / batch_size)


def calculate_caption_lengths(vocab, captions):
    lengths = 0
    for caption_tokens in captions:
        for token in caption_tokens:
            token = vocab.get_word(token.item())
            if token in ('<start>','<end>','<pad>'):
                continue
            else:
                lengths += 1
    return lengths
