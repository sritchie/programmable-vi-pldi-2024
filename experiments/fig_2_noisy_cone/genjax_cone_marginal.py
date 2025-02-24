#!/usr/bin/env python
# coding: utf-8


import jax
import jax.numpy as jnp
import jax.tree_util as jtu
import matplotlib.font_manager as font_manager
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams

import genjax
from genjax import vi

console = genjax.pretty()
key = jax.random.PRNGKey(314159)
sns.set_theme(style="white")
label_fontsize = 70  # Set the desired font size here


@genjax.gen
def model():
    x = vi.normal_reparam(0.0, 10.0) @ "x"
    y = vi.normal_reparam(0.0, 10.0) @ "y"
    rs = x**2 + y**2
    z = vi.normal_reparam(rs, 0.1 + (rs / 100.0)) @ "z"


# A more expressive variational family.
@genjax.gen
def expressive_variational_family(data, ϕ):
    z = data["z"]
    u = vi.uniform() @ "u"
    θ = 2 * jnp.pi * u
    log_σ1, log_σ2 = ϕ
    x = vi.normal_reparam(jnp.sqrt(z) * jnp.cos(θ), jnp.exp(log_σ1)) @ "x"
    y = vi.normal_reparam(jnp.sqrt(z) * jnp.sin(θ), jnp.exp(log_σ2)) @ "y"


marginal_q = vi.marginal(
    genjax.select("x", "y"), expressive_variational_family, lambda: vi.sir(1)
)

data = genjax.choice_map({"z": 5.0})
hvi_objective = vi.elbo(model, marginal_q, data)


# Training.
key = jax.random.PRNGKey(314159)
ϕ = (0.0, 0.0)
jitted = jax.jit(jax.vmap(hvi_objective.value_and_grad_estimate, in_axes=(0, None)))
losses = []
for i in range(0, 5000):
    key, sub_key = jax.random.split(key)
    sub_keys = jax.random.split(sub_key, 64)
    loss, (_, ((_, ϕ_grads), ())) = jitted(sub_keys, ((), ((data, ϕ), ())))
    ϕ = jtu.tree_map(lambda v, g: v + 1e-3 * jnp.mean(g), ϕ, ϕ_grads)
    if i % 1000 == 0:
        print(jnp.mean(loss))
    losses.append(jnp.mean(loss))


# ## Sampling from the prior variational family


key, sub_key = jax.random.split(key)
sub_keys = jax.random.split(sub_key, 50000)
ϕ_prior = (-0.3, -0.3)
scores, v_chm = jax.jit(jax.vmap(marginal_q.random_weighted, in_axes=(0, None, None)))(
    sub_keys, (data, ϕ_prior), ()
)


chm = v_chm.get_leaf_value()
x, y = chm["x"], chm["y"]
scores = jnp.exp(scores)

fig, ax = plt.subplots(figsize=(12, 12))
circle = patches.Circle((0.0, 0.0), radius=jnp.sqrt(5.0), fc="none", ec="black", lw=4)
ax.set_aspect("equal")
ax.scatter(x, y, c=scores, cmap="viridis", marker=".", s=20)
ax.add_patch(circle)
ax.text(2.0, 2.3, "z = 5.0", ha="center", va="center", fontsize=label_fontsize)
ax.set_xlim(-3, 3)
ax.set_ylim(-3, 3)
ax.set_xlabel("x", fontsize=label_fontsize)
ax.set_ylabel("y", fontsize=label_fontsize)
ax.set_xticks([])
ax.set_yticks([])
ax.yaxis.labelpad = 18  # adjust the value as needed
ax.yaxis.label.set_rotation(0)  # 90 degrees for vertical
plt.tight_layout()  # Adjusts subplot params so that subplots fit into the figure area
fig.savefig(
    "./figs/fig_2_untrained_expressive_variational_elbo_samples.pdf", format="pdf"
)

# ## Sampling from trained variational family


key, sub_key = jax.random.split(key)
sub_keys = jax.random.split(sub_key, 100000)
scores, v_chm = jax.jit(jax.vmap(marginal_q.random_weighted, in_axes=(0, None, None)))(
    sub_keys, (data, ϕ), ()
)


chm = v_chm.get_leaf_value()
x, y = chm["x"], chm["y"]
scores = jnp.exp(scores)
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_aspect("equal")
ax.scatter(x, y, c=scores, cmap="viridis", marker=".", s=20)
circle = patches.Circle((0.0, 0.0), radius=jnp.sqrt(5.0), fc="none", ec="black", lw=4)
ax.add_patch(circle)
ax.text(2.0, 2.3, "z = 5.0", ha="center", va="center", fontsize=label_fontsize)
ax.set_xlim(-3, 3)
ax.set_ylim(-3, 3)
ax.set_xlabel("x", fontsize=label_fontsize)
ax.set_ylabel("y", fontsize=label_fontsize)
ax.set_xticks([])
ax.set_yticks([])
ax.yaxis.labelpad = 18  # adjust the value as needed
ax.yaxis.label.set_rotation(0)  # 90 degrees for vertical
plt.tight_layout()  # Adjusts subplot params so that subplots fit into the figure area
fig.savefig("./figs/fig_2_hvi_expressive_variational_elbo_samples.pdf", format="pdf")

# ### Training with HVI & IWAE.

marginal_q = vi.marginal(
    genjax.select("x", "y"), expressive_variational_family, lambda: vi.sir(5)
)

hvi_objective = vi.iwae_elbo(model, marginal_q, data, 1)

# Training with IWAE.
key = jax.random.PRNGKey(314159)
ϕ = (0.0, 0.0)
jitted = jax.jit(jax.vmap(hvi_objective.value_and_grad_estimate, in_axes=(0, None)))
losses = []
for i in range(0, 5000):
    key, sub_key = jax.random.split(key)
    sub_keys = jax.random.split(sub_key, 64)
    loss, (_, ((_, ϕ_grads), ())) = jitted(sub_keys, ((), ((data, ϕ), ())))
    ϕ = jtu.tree_map(lambda v, g: v + 1e-3 * jnp.mean(g), ϕ, ϕ_grads)
    if i % 1000 == 0:
        print(jnp.mean(loss))
    losses.append(jnp.mean(loss))

key, sub_key = jax.random.split(key)
sub_keys = jax.random.split(sub_key, 100000)
scores, v_chm = jax.jit(jax.vmap(marginal_q.random_weighted, in_axes=(0, None, None)))(
    sub_keys, (data, ϕ), ()
)

chm = v_chm.get_leaf_value()
x, y = chm["x"], chm["y"]
scores = jnp.exp(scores)
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_aspect("equal")
ax.scatter(x, y, c=scores, cmap="viridis", marker=".", s=20)
circle = patches.Circle((0.0, 0.0), radius=jnp.sqrt(5.0), fc="none", ec="black", lw=4)
ax.add_patch(circle)
ax.text(2.0, 2.3, "z = 5.0", ha="center", va="center", fontsize=label_fontsize)
ax.set_xlim(-3, 3)
ax.set_ylim(-3, 3)
ax.set_xlabel("x", fontsize=label_fontsize)
ax.set_ylabel("y", fontsize=label_fontsize)
ax.set_xticks([])
ax.set_yticks([])
ax.yaxis.labelpad = 18  # adjust the value as needed
ax.yaxis.label.set_rotation(0)  # 90 degrees for vertical
plt.tight_layout()  # Adjusts subplot params so that subplots fit into the figure area

fig.savefig(
    "./figs/fig_2_iwhvi_trained_expressive_variational_elbo_samples.pdf", format="pdf"
)


marginal_q = vi.marginal(
    genjax.select("x", "y"), expressive_variational_family, lambda: vi.sir(5)
)

hvi_objective = vi.iwae_elbo(model, marginal_q, data, 5)

# Training with IWAE.
key = jax.random.PRNGKey(314159)
ϕ = (0.0, 0.0)
jitted = jax.jit(jax.vmap(hvi_objective.value_and_grad_estimate, in_axes=(0, None)))
losses = []
for i in range(0, 5000):
    key, sub_key = jax.random.split(key)
    sub_keys = jax.random.split(sub_key, 64)
    loss, (_, ((_, ϕ_grads), ())) = jitted(sub_keys, ((), ((data, ϕ), ())))
    ϕ = jtu.tree_map(lambda v, g: v + 1e-3 * jnp.mean(g), ϕ, ϕ_grads)
    if i % 1000 == 0:
        print(jnp.mean(loss))
    losses.append(jnp.mean(loss))

key, sub_key = jax.random.split(key)
sub_keys = jax.random.split(sub_key, 100000)
tgt = genjax.gensp.target(model, (), data)
approx = vi.sir(5, marginal_q, ((data, ϕ), ()))
v_chm = jax.jit(jax.vmap(approx.simulate, in_axes=(0, None)))(sub_keys, tgt)
chm = v_chm.get_leaf_value()
x, y = chm["x"], chm["y"]
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_aspect("equal")
ax.scatter(x, y, marker=".", s=20)
circle = patches.Circle((0.0, 0.0), radius=jnp.sqrt(5.0), fc="none", ec="black", lw=4)
ax.add_patch(circle)
ax.text(2.0, 2.3, "z = 5.0", ha="center", va="center", fontsize=label_fontsize)
ax.set_xlim(-3, 3)
ax.set_ylim(-3, 3)
ax.set_xlabel("x", fontsize=label_fontsize)
ax.set_ylabel("y", fontsize=label_fontsize)
ax.set_xticks([])
ax.set_yticks([])
ax.yaxis.labelpad = 18  # adjust the value as needed
ax.yaxis.label.set_rotation(0)  # 90 degrees for vertical
plt.tight_layout()  # Adjusts subplot params so that subplots fit into the figure area

fig.savefig(
    "./figs/fig_2_diwhvi_trained_expressive_variational_elbo_samples.pdf", format="pdf"
)
