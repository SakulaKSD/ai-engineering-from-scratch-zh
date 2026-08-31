import torch
import torch.nn as nn

model = nn.Linear(10, 1)  # 一个最简单的线性模型(10维进,1维出)
criterion = nn.MSELoss()  # 均方误差损失函数
optimizer = torch.optim.SGD(model.parameters(), lr=0.01)  # 随机梯度下降优化器

inputs = torch.randn(4, 10)  # 4 个样本，10维
labels = torch.randn(4, 1)  # 4 个答案


def training_step_v2(model, batch, criterion, optimizer):
    inputs, labels = batch
    outputs = model(inputs)
    loss = criterion(outputs, labels)

    loss.backward()
    if (
        loss.item() > 100
        or torch.isnan(loss)
        or torch.isnan(outputs).any()
        or torch.isinf(outputs).any()
    ):
        print(
            f"!!! 异常 detected: loss={loss.item():.4f}, has_nan={torch.isnan(loss).any()}, has_inf={torch.isinf(outputs).any()}"
        )
        breakpoint()

    optimizer.step()
    return loss


# 第一步正常训练
batch = (inputs, labels)
loss = training_step_v2(model, batch, criterion, optimizer)
print(f"第一步正常训练完成，loss = {loss.item():.4f}")

# 制造爆炸
optimizer = torch.optim.SGD(model.parameters(), lr=100.0)
print(f"lr 改成 {optimizer.param_groups[0]['lr']}")

for step in range(3):
    batch = (inputs, labels)
    loss = training_step_v2(model, batch, criterion, optimizer)
    print(f"step {step}: loss = {loss.item():.2f}")
