from agent import AlphaScholarTwoAgent, AlphaScholarMultiAgent
from utils import argparser 


if __name__ == "__main__":
    args = argparser()

    if args.agent == 'two':
        agent = AlphaScholarTwoAgent(platform=args.platform, log_path=args.log_path)
    elif args.agent == 'multi':
        agent = AlphaScholarMultiAgent(platform=args.platform, log_path=args.log_path)
    else:
        raise ValueError(f"Unsupported agent type: {args.agent}")

    final_report = agent.run()
    agent.save_report(final_report, file_path=args.report_path)