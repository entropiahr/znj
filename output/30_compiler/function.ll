; ModuleID = ""
target triple = "x86_64-unknown-linux-gnu"
target datalayout = ""

define i32 @"test"(i32 %"arg1", i32 %"arg2") 
{
entry:
  ret i32 %"arg1"
}

define i32 @"main"() 
{
entry:
  %"x" = call i32 @"test"(i32 1, i32 2)
  ret i32 %"x"
}
