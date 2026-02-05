export const NewProject = {
  projectTypes: [
    {
      id: 'projectName',
      name: '项目名称',
      type: 'text',
      default: '',
      placeholder: '请输入项目名称',
      required: true,
      description: '请输入新创建的项目名称'
    },
    {
      id: 'projectType',
      name: '项目类型',
      type: 'select',
      default: 'projects',
      options: [
        { value: 'projects', label: '单例项目(projects)' },
        { value: 'groups', label: '组项目(groups)'}
      ],
      description: '选择要创建的项目类型'
    },
    {
      id: 'projectDescription',
      name: '项目描述',
      type: 'textarea',
      default: '',
      placeholder: '请输入项目描述（可选）',
      description: '为项目添加描述信息'
    }
  ]
};