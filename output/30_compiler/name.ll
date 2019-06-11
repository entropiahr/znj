; ModuleID = ""
target triple = "x86_64-unknown-linux-gnu"
target datalayout = ""

define i32 @"main"() 
{
entry:
  %"test.1" = add i32 1, 1
  %"test.2" = add i32 1, %"test.1"
  ret i32 %"test.2"
}
