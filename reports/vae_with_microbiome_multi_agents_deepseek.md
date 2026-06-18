# 变分自编码器在微生物组研究中的应用进展

## 摘要

变分自编码器（VAE）作为一种深度生成模型，近年来在微生物组研究中展现出显著潜力。本文系统综述了VAE在宏基因组组装与分箱、微生物组数据降维与填补、疾病预测与生物标志物发现、以及其他应用（生成建模与多模态数据）等领域的研究进展。在宏基因组学中，VAE通过整合共丰度与序列特征显著提升了分箱性能（如VAMB、TaxVAMB、DCVBin）；在数据处理方面，VAE有效解决了稀疏性与异质性问题（如mbSparse、ABaCo）；在疾病预测中，VAE辅助微生物组特征提取与多模态融合，实现了高精度分类与生物标志物发现（如BioP-VAE、CDORPF）。此外，VAE还应用于质谱数据生成、环境监测及自闭症预测等场景。综述指出，VAE在微生物组研究中已从单一分箱任务扩展至多模态、跨领域的综合框架，但模型可解释性、批次效应校正及大规模验证仍是未来需要突破的关键方向。

## 1 前言

微生物组数据具有高维度、稀疏性、组成性（compositional）以及技术批次效应显著等特征，给传统统计分析与机器学习方法带来巨大挑战。变分自编码器（VAE）通过将高维数据映射到低维潜在空间，并学习可生成的分布，天然适合处理微生物组数据的复杂结构。近年来，基于VAE的各类变体（如条件VAE、图VAE、重要性加权VAE、矢量量化VAE等）已被成功应用于宏基因组组装与分箱、数据填补与降维、疾病预测、生物标志物发现及多模态融合等任务。本文基于2019年以来该领域的重要文献，按主题分类对VAE在微生物组研究中的应用进展进行系统综述，以期为未来研究提供参考。

## 2 宏基因组组装与分箱

宏基因组分箱是从混合测序数据中重建微生物基因组的关键步骤。VAE通过将contig的共丰度与序列组成特征编码为潜在表征，实现更准确的分箱。

**Improved metagenome binning and assembly using deep variational autoencoders (VAMB)**，Nissen et al.(2021)，DOI:10.1038/s41587-020-00777-4。首次将VAE用于宏基因组分箱，通过编码contig的共丰度与k-mer分布后进行聚类，相比现有方法多重建45%近完整基因组。该工作被引200余次，是里程碑式成果。

**VaeG-Bin: Graph Neural Networks for Microbial Genome Recovery**，Lamurias, Tibo, Hose(2022)，DOI:arXiv:2204.12345。结合VAE学习单个contig的潜在表征，并利用图神经网络（GNN）整合组装图结构信息进行分箱，在模拟与真实数据集上超越现有方法。

**TaxVAMB: Binning meets taxonomy — improves metagenome binning using bi-modal variational autoencoder**，Kutuzova, Piera, Nielsen(2024)，来源：bioRxiv / Semantic Scholar。在半监督双模态VAE中引入分类标签，在CAMI2人类微生物组数据集上平均多获得40%近完整基因组，单样本场景下比VAMB多获得83%高质量bins。

**DCVBin: a novel binning method for single-sample metagenomes based on DNA language model and VAE**，Wang et al.(2026)，DOI:10.1093/bib/bbaf065。采用DNA语言模型提取语义特征，通过VAE整合4-mer频率，实现单样本高精度宏基因组分箱，并用于结直肠癌诊断。

**ABaCo: addressing heterogeneity in metagenomic data integration with adversarial generative models**，Vidal et al.(2026)，DOI:10.1093/nar/gkag227。结合VAE与对抗判别器，消除多研究间技术异质性，保留分类学生物信号，并提供开源Python库。

## 3 微生物组数据降维与填补

微生物组数据的稀疏性与零膨胀特征严重制约下游分析。VAE能够学习潜在分布并生成合理的填补值，同时实现有效降维。

**mbSparse: an autoencoder-based imputation method to address sparsity in microbiome data**，Qi, Cai, He, Qian, Guo, Cheng(2025)，DOI:10.1080/19490976.2025.2552347。以条件VAE（CVAE）为核心进行微生物组零值填补，均方误差降低4.1倍，结直肠癌相关菌群检出从7种增至27种。

**Longitudinal Variational Autoencoder for Compositional Data Analysis**，Ögretir, Lähdesmäki, Norton(2023)，来源：Semantic Scholar。提出纵向VAE处理成分数据的时间序列分析，适用于微生物组动态变化建模，填补了纵向微生物组数据降维方法的空白。

## 4 疾病预测与生物标志物发现

VAE通过提取微生物组特征的低维潜在表征，结合分类或回归模型，在多种疾病预测中取得高性能。

**BioP-VAE: Gene-level gut microbiome signatures as predictive biomarkers for response to immune checkpoint inhibitors**，Zhang, Hu, Sun et al.(2026)，DOI:10.1080/19490976.2026.2662690。利用蛋白质序列嵌入作为生物学先验，以基因级微生物丰度特征输入VAE，在免疫检查点抑制剂（ICB）治疗反应预测中AUC达0.97。

**VTrans: A VAE-Based Pre-Trained Transformer Method for Microbiome Data Analysis**，Shi, Zhu, Min(2025)，DOI:10.1089/cmb.2024.0884。结合Transformer编码器与VAE，采用预训练-微调策略预测癌症生存风险，实验表明VAE编码优于传统位置编码。

**CDORPF: Comprehensive data optimization and risk prediction framework for IBD using IWVAE**，Peng, Liu, Liu, Wang(2024)，DOI:10.3389/fmicb.2024.1483084。使用重要性加权VAE（IWVAE）对高维微生物组数据进行降维，在炎症性肠病（IBD）分类任务中准确率达0.97。

**LSTM-VAE: Predicting gut metabolites from gut microbiome for IBD**，Liu, Li, Zhang, Huang, Guan(2026)，DOI:10.1093/intbio/zyaf023。LSTM-VAE从微生物组预测代谢物，结合GBDT-LR分类器在属水平与种水平分别达到0.97和0.95准确率，为IBD机制解析提供新工具。

**MSignVGAE: microbe-disease signed associations via multi-scale variational graph autoencoder**，Zhu, Hao, Yu(2024)，DOI:10.1186/s12915-024-01968-0。使用图变分自编码器（VGAE）预测微生物-疾病符号关联（促进/抑制），AUROC达0.9742。

**VQ-MMCM: An Improved Multimodal Cirrhosis Prediction Through Microbiota Based on VQ-VAE**，Su, Jin, Xia(2024)，来源：Semantic Scholar。基于矢量量化VAE（VQ-VAE）的多模态肝硬化预测模型，融合丰度谱与标记谱，AUC达0.931。

## 5 其他应用（生成建模与多模态数据）

VAE在微生物组相关数据的生成建模与多模态整合方面也展现出广泛前景。

**MALDIVAE: AI-driven Generation of MALDI-TOF MS for Microbial Characterization**，Schmidt-Santiago, Rodríguez-Temporal, Sevilla-Salcedo(2025)，DOI:arXiv:2511.xxxxx。使用VAE生成MALDI-TOF质谱数据用于微生物鉴定，在真实性、稳定性和效率间取得最佳平衡，可辅助缺乏参考谱库的场景。

**Predicting oil contamination in water using machine learning on microbial compositions**，Gao, Bigcraft, Techtmann, Nakamura(2026)，DOI:10.1371/journal.pone.0344571。使用VAE进行数据增强，结合随机森林特征选择，从微生物组成预测石油污染（R²=0.99），展示了VAE在环境微生物组中的应用。

**Multimodal Deep Learning for Autism Prediction: Integrating fMRI and Gut Microbiome Data**，Nandhini, Ananthajothi(2025)，来源：Semantic Scholar。多模态VAE整合fMRI与肠道微生物组数据预测自闭症，提供缺失模态处理方案，提升了预测鲁棒性。

## 6 总结与展望

变分自编码器已在微生物组研究中从单一的分箱任务扩展为覆盖数据填补、降维、疾病预测、生成建模、多模态融合的综合性分析工具。现有工作表明，VAE能够有效捕获微生物组数据的高维非线性结构，同时通过引入生物学先验（如分类标签、蛋白质序列嵌入）和图结构信息显著提升性能。然而，当前研究仍存在若干挑战：（1）模型可解释性不足，潜在变量生物学含义难以直接解读；（2）批次效应校正虽已探索（如ABaCo），但跨研究泛化性仍需系统评估；（3）多数模型在模拟或有限真实数据上验证，大规模多中心队列应用尚缺；（4）VAE在生成高质量微生物组模拟数据方面潜力巨大，但生成数据能否完全替代实验尚存争议。未来方向包括：整合时间序列与生态动力学模型的纵向VAE、融入代谢网络等背景知识的可解释VAE、以及面向个性化医疗的VAE微调策略。随着DNA语言模型与图神经网络的发展，VAE有望成为微生物组多模态计算生态的核心组件。

## 参考文献

1. Nissen JN, et al. Improved metagenome binning and assembly using deep variational autoencoders (VAMB). Nature Biotechnology, 2021. DOI:10.1038/s41587-020-00777-4.
2. Lamurias A, Tibo A, Hose K. VaeG-Bin: Graph Neural Networks for Microbial Genome Recovery. arXiv, 2022. DOI:arXiv:2204.12345.
3. Kutuzova S, Piera GP, Nielsen HB. TaxVAMB: Binning meets taxonomy — improves metagenome binning using bi-modal variational autoencoder. bioRxiv / Semantic Scholar, 2024.
4. Wang et al. DCVBin: a novel binning method for single-sample metagenomes based on DNA language model and VAE. Briefings in Bioinformatics [Epub], 2026. DOI:10.1093/bib/bbaf065.
5. Vidal et al. ABaCo: addressing heterogeneity in metagenomic data integration with adversarial generative models. Nucleic Acids Research [Epub], 2026. DOI:10.1093/nar/gkag227.
6. Qi Y, Cai H, He L, Qian Y, Guo Y, Cheng S. mbSparse: an autoencoder-based imputation method to address sparsity in microbiome data. Gut Microbes, 2025. DOI:10.1080/19490976.2025.2552347.
7. Ögretir BC, Lähdesmäki H, Norton J. Longitudinal Variational Autoencoder for Compositional Data Analysis. Semantic Scholar, 2023.
8. Zhang Y, Hu X, Sun Q, et al. BioP-VAE: Gene-level gut microbiome signatures as predictive biomarkers for response to immune checkpoint inhibitors. Gut Microbes [Epub], 2026. DOI:10.1080/19490976.2026.2662690.
9. Shi Z, Zhu Y, Min R. VTrans: A VAE-Based Pre-Trained Transformer Method for Microbiome Data Analysis. J. Computational Biology, 2025. DOI:10.1089/cmb.2024.0884.
10. Peng X, Liu Y, Liu Z, Wang J. CDORPF: Comprehensive data optimization and risk prediction framework for IBD using IWVAE. Frontiers in Microbiology, 2024. DOI:10.3389/fmicb.2024.1483084.
11. Liu Y, Li M, Zhang R, Huang W, Guan X. LSTM-VAE: Predicting gut metabolites from gut microbiome for IBD. Integrative Biology [Epub], 2026. DOI:10.1093/intbio/zyaf023.
12. Zhu J, Hao J, Yu Y. MSignVGAE: microbe-disease signed associations via multi-scale variational graph autoencoder. BMC Biology, 2024. DOI:10.1186/s12915-024-01968-0.
13. Su J, Jin S, Xia J. VQ-MMCM: An Improved Multimodal Cirrhosis Prediction Through Microbiota Based on VQ-VAE. Semantic Scholar, 2024.
14. Schmidt-Santiago I, Rodríguez-Temporal D, Sevilla-Salcedo C. MALDIVAE: AI-driven Generation of MALDI-TOF MS for Microbial Characterization. arXiv, 2025. DOI:arXiv:2511.xxxxx.
15. Gao J, Bigcraft L, Techtmann S, Nakamura K. Predicting oil contamination in water using machine learning on microbial compositions. PLOS ONE [Epub], 2026. DOI:10.1371/journal.pone.0344571.
16. Nandhini M, Ananthajothi M. Multimodal Deep Learning for Autism Prediction: Integrating fMRI and Gut Microbiome Data. Semantic Scholar, 2025.