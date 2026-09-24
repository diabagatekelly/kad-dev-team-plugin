PASS

`OrderSummaryFormatter.describe` is explicitly categorized as feature
envy, naming the shape correctly: deep reads into `order`'s fields versus
never touching `this.locale`, the class's only state.
