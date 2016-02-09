import Text.Pandoc.JSON

-- Inspiration for this haskell script:
-- https://groups.google.com/forum/#!msg/pandoc-discuss/FzLrhk0vVbU/quKJlnAWI4sJ
--
-- To compile: ghc --make -v insert_pagebreaks_filter.hs
-- libghc-pandoc-dev is required to compile

pgBrkXml :: String

pgBrkXml = "<w:p><w:r><w:br w:type=\"page\"/></w:r></w:p>"

pgBrkBlock :: Block
pgBrkBlock = RawBlock (Format "openxml") pgBrkXml

insertPgBrks :: Block -> Block

insertPgBrks (Para [RawInline (Format "tex") "\\newpage"]) = pgBrkBlock
insertPgBrks blk = blk

main = toJSONFilter insertPgBrks
