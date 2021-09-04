Attribute VB_Name = "Module1"
Sub Macro_Format()
Attribute Macro_Format.VB_Description = "Macro_Format"
Attribute Macro_Format.VB_ProcData.VB_Invoke_Func = "m\n14"
'
' Macro_Format Macro
' Macro_Format
'
' Keyboard Shortcut: Ctrl+m
'
	Columns("O:O").Cut
    Columns("E:E").Insert Shift:=xlToRight
    Columns("P:P").Cut
    Columns("F:F").Insert Shift:=xlToRight
	
    Range("A1:U1632").Select
    Range("O6").Activate
    Selection.Columns.AutoFit
    ActiveSheet.ListObjects.Add(xlSrcRange, Range("$A$1:$P$1632"), , xlYes).Name = _
        "Table1"
    Range("Table1[#All]").Select
    ActiveSheet.ListObjects("Table1").TableStyle = "TableStyleLight12"
    Selection.FormatConditions.Add Type:=xlExpression, Formula1:="=$M1>5"
    Selection.FormatConditions(Selection.FormatConditions.Count).SetFirstPriority
    With Selection.FormatConditions(1).Interior
        .PatternColorIndex = xlAutomatic
        .ThemeColor = xlThemeColorAccent3
        .TintAndShade = 0.399945066682943
    End With
    Selection.FormatConditions(1).StopIfTrue = False
    Selection.FormatConditions.Add Type:=xlExpression, Formula1:="=$M1<-5"
    Selection.FormatConditions(Selection.FormatConditions.Count).SetFirstPriority
    With Selection.FormatConditions(1).Interior
        .PatternColorIndex = xlAutomatic
        .ThemeColor = xlThemeColorAccent6
        .TintAndShade = 0.599963377788629
    End With
    Selection.FormatConditions(1).StopIfTrue = False
    Range("F3").Select
	
End Sub
