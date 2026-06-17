# 基于深度学习的宏基因组学分析方法与应用进展综述

## 摘要

宏基因组学通过直接测序环境样本中的全部微生物遗传物质，为解析微生物群落的结构、功能及其与宿主健康的关系提供了重要手段。然而，宏基因组数据具有高维度、稀疏性和异质性等特点，传统分析方法面临诸多挑战。近年来，深度学习技术，特别是变分自编码器（VAE）、生成对抗网络（GAN）和图神经网络（GNN）等，在宏基因组数据处理中展现出显著优势。本文系统回顾了2021—2026年间深度学习方法在宏基因组数据分箱（binning）、数据整合与异质性校正、数据预处理与增强、疾病预测与标志物发现以及微生物-疾病关联分析等五个主题方向上的最新进展。共纳入16篇代表性文献，涵盖基于VAE的改进分箱方法、对抗生成模型整合策略、零膨胀数据插补框架以及可解释的预测模型等。综述表明，深度学习技术正从单一任务建模向多模态、可解释和稳健性方向演进，为宏基因组学精准分析提供了强有力的工具。最后，本文讨论了当前方法的局限性并展望了未来发展方向。

## 前言

宏基因组学的发展使研究者能够不依赖培养直接获取微生物群落的遗传信息，从而揭示微生物在人体健康、环境生态及农业生产中的关键作用。然而，宏基因组数据固有的特性——如物种组成的高维稀疏性、测序深度不均导致的零膨胀、不同批次或平台间的异质性，以及微生物与宿主相互作用的复杂性——对传统统计分析构成了严峻挑战。近年来，以深度学习为核心的人工智能技术凭借其强大的非线性表征能力和自动特征提取优势，逐渐渗透到宏基因组分析的各个环节。其中，变分自编码器（VAE）、生成对抗网络（GAN）、图卷积网络（GCN）及Transformer等模型在数据降维、缺失值填补、数据增强、聚类分箱和疾病预测等方面取得了突破性进展。本文围绕宏基因组学分析中五个关键主题——宏基因组数据分箱（Binning）、多源数据整合与异质性校正、数据预处理与增强、疾病预测与生物标志物发现、微生物-疾病关联分析——对近期代表性研究进行梳理与评述，旨在呈现该领域的最新动态，并为后续研究提供参考。

## 主题分节综述

### 一、宏基因组Binning

宏基因组Binning是将测序得到的混杂序列片段按微生物基因组进行聚类，是重建未培养微生物基因组的核心步骤。传统方法依赖序列组成和丰度特征，而深度学习方法通过自动学习深层特征显著提升了分箱质量。

**（1）Improved metagenome binning and assembly using deep variational autoencoders (VAMB)**，Nissen JN等(2021)，DOI: 10.1038/s41587-020-00777-4。该研究提出VAMB（Variational Autoencoders for Metagenomic Binning），利用深度变分自编码器同时学习序列的组成和丰度特征，在大规模宏基因组数据集上显著提高了分箱的召回率和纯度，尤其对于低丰度物种的恢复效果突出。

**（2）DCVBin: a novel binning method for single-sample metagenomes based on DNA language model and variational autoencoder**，Wang等(2026)，DOI: 10.1093/bib/bbag241。该工作针对单样本宏基因组分箱难题，将DNA语言模型与变分自编码器相融合，通过预训练的核苷上下文表示增强序列特征提取，在低深度样本中表现出优于传统方法的稳健性。

**（3）Graph Neural Networks for Microbial Genome Recovery (VaeG-Bin)**，Lamurias A等(2022)，arXiv预印本。该研究提出VaeG-Bin，首次将图神经网络引入宏基因组分箱，将重叠群（contigs）间的共丰度和序列相似性构建为图结构，利用变分图自编码器学习节点嵌入，通过图聚类实现基因组回收，有效利用了拓扑信息。

**（4）A Deep Clustering-based Novel Approach for Binning of Metagenomics Data**，Madival等(2023)，DOI: 10.2174/1389202923666220928150100。该研究采用深度聚类框架，将自编码器降维与聚类损失联合优化，同时学习低维表示和聚类分配，避免了传统两步法的信息损失，在模拟和真实数据集上验证了其分箱准确性。

### 二、数据整合与异质性校正

多批次或多来源宏基因组数据的整合面临显著的批次效应和异质性挑战。深度学习生成模型能够学习数据潜在分布，实现无偏整合。

**（5）ABaCo: addressing heterogeneity challenges in metagenomic data integration with adversarial generative models**，Vidal等(2026)，DOI: 10.1093/nar/gkag227。ABaCo引入对抗生成网络，通过生成器学习可迁移的潜在特征并利用判别器消除批次来源信息，从而实现在保留生物学变异的同时校正技术异质性，在跨数据集微生物丰度整合中表现出色。

**（6）Deep learning enabled integration of tumor microenvironment microbial profiles and host gene expressions for interpretable survival subtyping (ASD-cancer)**，Zhang等(2024)，DOI: 10.1128/msystems.01395-24。该研究聚焦肿瘤微环境，构建多模态深度学习模型整合微生物丰度与宿主基因表达数据，通过注意力机制实现可解释的生存亚型划分，揭示了微生物-宿主相互作用对预后的影响。

### 三、数据预处理与增强

宏基因组数据普遍存在零膨胀和稀疏性问题，影响下游分析稳定性；此外，样本量不足也限制了深度学习模型的泛化能力。因此，数据插补和数据增强成为关键预处理步骤。

**（7）mbSparse: an autoencoder-based imputation method to address sparsity in microbiome data**，Qi等(2025)，DOI: 10.1080/19490976.2025.2552347。mbSparse利用自编码器学习微生物条件分布，对零值进行概率插补，在保持物种相关性的同时有效恢复了缺失丰度，优于传统的乘法插补和线性模型。

**（8）BMDD: A probabilistic framework for accurate imputation of zero-inflated microbiome sequencing data**，Zhou等(2025)，DOI: 10.1371/journal.pcbi.1013124。BMDD提出了基于贝叶斯概率框架的插补方法，结合混合分布建模和变分推断，能够区分“结构零”（生物不存在）与“采样零”（未检测到），显著提升插补的生物学合理性。

**（9）Comprehensive data optimization and risk prediction framework (CDORPF) using IWVAE for IBD prediction**，Peng等(2024)，DOI: 10.3389/fmicb.2024.1483084。该研究将改进的变分自编码器（IWVAE）用于数据优化与风险预测，在炎症性肠病（IBD）预测中同时实现数据降噪和疾病标志物识别，验证了数据增强对模型性能的提升作用。

**（16）phylaGAN: data augmentation through conditional GANs and autoencoders for improving disease prediction**，Sharma等(2024)，DOI: 10.1093/bioinformatics/btae161。phylaGAN结合条件生成对抗网络与自编码器，根据真实样本的门级丰度分布生成人工样本，有效扩充了小型宏基因组数据集，在保持群落结构的同时提高了疾病二分类的F1分数。

### 四、疾病预测与标志物发现

基于微生物组特征构建疾病预测模型是转化医学的核心目标。深度学习可自动筛选与疾病相关的微生物标志物，并整合代谢活性等多维信息提升预测性能。

**（10）BioP-VAE: Gene-level gut microbiome signatures as predictive biomarkers for response to immune checkpoint inhibitors**，Zhang等(2026)，DOI: 10.1080/19490976.2026.2662690。BioP-VAE以基因级功能特征代替传统物种丰度，利用变分自编码器提取肠道微生物组中与免疫检查点抑制剂疗效相关的功能标志物，实现了跨队列的可靠预测。

**（11）VTrans: A VAE-Based Pre-Trained Transformer Method for Microbiome Data Analysis**，Shi等(2025)，DOI: 10.1089/cmb.2024.0884。VTrans将VAE与Transformer预训练范式结合，首先在无标签微生物数据上学习通用序列表示，再通过微调适应特定疾病预测任务，缓解了小样本过拟合问题，在IBD和糖尿病数据集中表现优异。

**（12）MicroKPNN: Incorporating metabolic activity, taxonomy and community structure to improve microbiome-based predictive models**，Monshizadeh & Ye (2024)，DOI: 10.1080/19490976.2024.2302076。MicroKPNN构建了基于核方法的深度神经网络，融合微生物分类信息、代谢通路活性（通过KEGG预测）以及群落共现结构，输出加权预测结果，为个性化疾病风险评估提供了新范式。

**（13）Predicting gut metabolites from gut microbiome using LSTM-VAE with LIME interpretability**，Liu等(2026)，DOI: 10.1093/intbio/zyaf023。该研究将LSTM与VAE组合用于从宏基因组数据预测肠道代谢物浓度，并引入LIME（局部可解释模型）分析关键微生物类群贡献，实现了预测与可解释性的兼顾。

### 五、微生物-疾病关联分析

微生物与疾病的关联挖掘有助于发现潜在因果机制。传统关联分析依赖于线性相关，而图神经网络和深度因子分解模型能够捕捉高阶非线性关系。

**（14）MSignVGAE: Identification of microbe-disease signed associations via multi-scale variational graph autoencoder**，Zhu等(2024)，DOI: 10.1186/s12915-024-01968-0。MSignVGAE构建微生物-疾病二部图，利用多尺度变分图自编码器学习节点表示，并引入符号边预测机制区分正向（促进）和负向（抑制）关联，在已知关联恢复和未知关联预测中均优于传统图方法。

**（15）DSAE_RF: Predicting potential microbe-disease associations based on multi-source features and deep learning**，Wang等(2023)，DOI: 10.1093/bib/bbad255。DSAE_RF整合微生物功能相似性、疾病语义相似性和已知关联信息，通过深度堆叠自编码器提取深层特征，结合随机森林分类器预测新的微生物-疾病关联，在基准数据集上获得高AUC值。

## 总结与展望

本文系统综述了深度学习技术在宏基因组学分析中的最新应用，涵盖数据分箱、异质性校正、预处理增强、疾病预测及关联挖掘五大方向。总体而言，该领域呈现出以下趋势：第一，从单一模型向混合架构演进，如VAE与Transformer、图神经网络的结合，提升了表达能力和泛化性；第二，可解释性日益受到重视，LIME、注意力机制等方法使“黑箱”模型逐步透明化，增强了生物可信度；第三，多模态数据融合成为热点，微生物丰度与宿主基因表达、代谢谱等信息的整合为精准医学提供了更全面的视角。

然而，当前方法仍面临若干挑战：一是高质量标注数据匮乏，尤其罕见病和极端环境样本稀缺，亟需发展更鲁棒的半监督或无监督学习策略；二是现有模型在跨数据集、跨平台间的泛化能力有限，批次效应的深度校正方法仍需标准化；三是从关联挖掘到因果推断的跨越尚未实现，深度生成模型与因果推理的结合可能是未来突破点。随着多组学技术的普及和计算框架的持续优化，深度学习有望在微生物组驱动的个性化诊疗、生态功能预测等方向发挥更核心的作用。

## 参考文献

1. Nissen JN, Johansen J, Allesøe RL, et al. Improved metagenome binning and assembly using deep variational autoencoders. *Nature Biotechnology*, 2021, 39(5): 555-560. DOI: 10.1038/s41587-020-00777-4.
2. Wang, Liu, Liu, et al. DCVBin: a novel binning method for single-sample metagenomes based on DNA language model and variational autoencoder. *Briefings in Bioinformatics*, 2026. DOI: 10.1093/bib/bbag241.
3. Lamurias A, Tibo A, Hose K. Graph Neural Networks for Microbial Genome Recovery (VaeG-Bin). *arXiv preprint*, 2022.
4. Madival, Mishra, Sharma, et al. A Deep Clustering-based Novel Approach for Binning of Metagenomics Data. *Current Genomics*, 2023, 24(1): 44-55. DOI: 10.2174/1389202923666220928150100.
5. Vidal, Phanthanourak, Gharib, et al. ABaCo: addressing heterogeneity challenges in metagenomic data integration with adversarial generative models. *Nucleic Acids Research*, 2026. DOI: 10.1093/nar/gkag227.
6. Zhang, Xiong, Cheng, et al. Deep learning enabled integration of tumor microenvironment microbial profiles and host gene expressions for interpretable survival subtyping (ASD-cancer). *mSystems*, 2024, 9(12): e01395-24. DOI: 10.1128/msystems.01395-24.
7. Qi, Cai, He, et al. mbSparse: an autoencoder-based imputation method to address sparsity in microbiome data. *Gut Microbes*, 2025. DOI: 10.1080/19490976.2025.2552347.
8. Zhou, Chen, Zhang. BMDD: A probabilistic framework for accurate imputation of zero-inflated microbiome sequencing data. *PLoS Computational Biology*, 2025. DOI: 10.1371/journal.pcbi.1013124.
9. Peng, Liu, Liu, et al. Comprehensive data optimization and risk prediction framework (CDORPF) using IWVAE for IBD prediction. *Frontiers in Microbiology*, 2024, 15: 1483084. DOI: 10.3389/fmicb.2024.1483084.
10. Zhang, Hu, Sun, et al. BioP-VAE: Gene-level gut microbiome signatures as predictive biomarkers for response to immune checkpoint inhibitors. *Gut Microbes*, 2026. DOI: 10.1080/19490976.2026.2662690.
11. Shi, Zhu, Min. VTrans: A VAE-Based Pre-Trained Transformer Method for Microbiome Data Analysis. *Journal of Computational Biology*, 2025. DOI: 10.1089/cmb.2024.0884.
12. Monshizadeh, Ye. MicroKPNN: Incorporating metabolic activity, taxonomy and community structure to improve microbiome-based predictive models. *Gut Microbes*, 2024. DOI: 10.1080/19490976.2024.2302076.
13. Liu, Li, Zhang, et al. Predicting gut metabolites from gut microbiome using LSTM-VAE with LIME interpretability. *Integrative Biology*, 2026. DOI: 10.1093/intbio/zyaf023.
14. Zhu, Hao, Yu. MSignVGAE: Identification of microbe-disease signed associations via multi-scale variational graph autoencoder. *BMC Biology*, 2024. DOI: 10.1186/s12915-024-01968-0.
15. Wang, Wang, Xuan, et al. DSAE_RF: Predicting potential microbe-disease associations based on multi-source features and deep learning. *Briefings in Bioinformatics*, 2023. DOI: 10.1093/bib/bbad255.
16. Sharma, Lou, Xu. phylaGAN: data augmentation through conditional GANs and autoencoders for improving disease prediction. *Bioinformatics*, 2024. DOI: 10.1093/bioinformatics/btae161.