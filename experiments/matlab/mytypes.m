function T = mytypes(dt,b,frac)
  switch dt
    case 'double'
      T = double([]);
    case 'single'
      T = single([]);
    case 'fixed'
      T = fi([],true,b,frac);
    case 'wfixed'
      F = fimath('OverflowAction','Wrap');
      T = fi([],true,b,frac,'fimath',F);
    case 'scaled'
      T = fi([],true,16,15,'DataType','ScaledDouble');
  end
end
