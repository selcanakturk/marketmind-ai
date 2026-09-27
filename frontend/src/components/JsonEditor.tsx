import { useEffect, useState } from 'react'

export function JsonEditor<T>({ id, label, value, onChange, help }: { id:string; label:string; value:T; onChange:(value:T)=>void; help?:string }) {
  const [text,setText]=useState(()=>JSON.stringify(value,null,2)); const [error,setError]=useState('')
  useEffect(()=>setText(JSON.stringify(value,null,2)),[value])
  const update=(next:string)=>{setText(next);try{onChange(JSON.parse(next) as T);setError('')}catch{setError('Enter valid JSON before running.')}}
  return <div className="field"><div className="editor-toolbar"><label htmlFor={id}>{label}</label><span className="small muted">{Array.isArray(value)?`${value.length} rows`:''}</span></div><textarea id={id} value={text} onChange={e=>update(e.target.value)} aria-invalid={!!error} aria-describedby={`${id}-help ${id}-error`} spellCheck={false}/>{help&&<small id={`${id}-help`}>{help}</small>}{error&&<span id={`${id}-error`} className="error-text" role="alert">{error}</span>}</div>
}
