results = analyzer.analyze_directory(directory)

    # Save report
    output_path = Path(args.output)
    analyzer.save_report(results, output_path)

    # Display summary if requested
    if args.summary or True:  # Always show summary
        summary = analyzer.generate_summary(results)
        print(summary)
