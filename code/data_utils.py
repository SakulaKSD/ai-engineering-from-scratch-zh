"""可复用的数据加载与缓存工具（Phase 0-09）。"""

from datasets import load_dataset


def load_imdb(split: str = "train"):
    """加载 IMDB 数据集（自动走缓存）。"""
    return load_dataset("stanfordnlp/imdb", split=split)


def split_train_val_test(dataset, val_ratio=0.1, test_ratio=0.2, seed=42):
    """把数据集切成 train / val / test 三份（固定种子保证可复现）。"""
    split = dataset.train_test_split(test_size=test_ratio, seed=seed)
    train_val = split["train"].train_test_split(
        test_size=val_ratio / (1 - test_ratio), seed=seed
    )
    return train_val["train"], train_val["test"], split["test"]


def summarize(dataset, name: str):
    """打印数据集摘要。"""
    print(f"{name}: {len(dataset)} 条样本")
    if len(dataset) > 0:
        print(f"  第一条特征: {list(dataset[0].keys())}")
        print(f"  第一条内容: {str(dataset[0])[:80]}...")


if __name__ == "__main__":
    print("加载 IMDB ...")
    ds = load_imdb("train")

    print("\n划分 train/val/test ...")
    train_ds, val_ds, test_ds = split_train_val_test(ds)

    summarize(train_ds, "Train")
    summarize(val_ds, "Val")
    summarize(test_ds, "Test")
    print("\n数据工具验证完成 ✅")
