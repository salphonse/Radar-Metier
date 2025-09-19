# model.py
import torch
import torch.nn as nn
import torch.nn.functional as F
import math

class JobProfileTransformer(nn.Module):
    def __init__(self, n_skills, n_jobs, emb_dim=64, n_heads=4, n_layers=2, max_len=88):
        super().__init__()
        self.skill_emb = nn.Embedding(n_skills, emb_dim)
        self.pos_emb = nn.Parameter(torch.randn(1, max_len, emb_dim))
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=emb_dim, nhead=n_heads, dim_feedforward=256, batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.job_emb = nn.Embedding(n_jobs, emb_dim)

    def encode_profile(self, skills, weights=None):
        batch_size, seq_len = skills.shape
        pos_emb = self.pos_emb[:, :seq_len, :] if seq_len <= self.pos_emb.size(1) \
            else self.pos_emb.repeat(1, math.ceil(seq_len / self.pos_emb.size(1)), 1)[:, :seq_len, :]
        skills_emb = self.skill_emb(skills) + pos_emb
        if weights is not None:
            skills_emb = skills_emb * weights.unsqueeze(-1)
        mask = (skills == 0)
        v = self.encoder(skills_emb, src_key_padding_mask=mask)
        return F.normalize(v.mean(dim=1), dim=1)

    def encode_job(self, job_ids):
        return F.normalize(self.job_emb(job_ids), dim=1)

